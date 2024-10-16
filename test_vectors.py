import cv2
import numpy as np
from vectors import LineVec, CircleVec, PencilVec, RectangleVec
from layout import COLORS_RGB
from board_view import BoardView, get_board_view
from tempfile import mkdtemp
from vector_manager import VectorManager


def test_vectors(show=True):
    """
    Create a vector manager, add some vectors to it.
    Save it's state, create a new vector manager, load the state, check that the vectors are the same.
    Render the vectors to a frame if display_size is not None.
    """
    display_size = (640, 480)

    VECS = [PencilVec, LineVec, CircleVec, RectangleVec]
    COLORS = ['red', 'green', 'blue', 'black']
    BKG = 'off_white'
    w, h = display_size
    n_each = 50  # create this many test vectors
    n_pts = 20  # number of points to add to each vector
    dist_sd = 3  # standard deviation of the distance between points (random walk)
    vectors = []
    all_pts = []
    vm = VectorManager(None)

    def _make_pts():
        """
        :returns: n_pts x 2 array of points, random walk
        """

        pts = np.zeros((n_pts, 2))
        pts[0] = np.random.normal(0, dist_sd * n_pts, 2)
        for i in range(1, n_pts):
            pts[i] = pts[i-1] + np.random.normal(0, dist_sd, 2)
        return pts

    for vec_t in VECS:
        for _ in range(n_each):
            color = COLORS_RGB[np.random.choice(COLORS)]
            vec = vec_t(color, thickness=np.random.randint(1, 5))
            points = _make_pts()
            for pt in points:
                vec.add_point(pt)
            vec.finalize()
            vectors.append(vec)
            vm.add_vector(vec)
            all_pts.append(points)

    all_pts = np.vstack(all_pts)
    view = get_board_view(all_pts, display_size)
    frame = (np.zeros((display_size[1], display_size[0], 3)) + COLORS_RGB[BKG]).astype(np.uint8)

    vm.render(frame, view)

    # save it
    temp_dir = mkdtemp()
    save_file = temp_dir + '/test_vectors.json'
    vm.save(save_file)

    # Show different views after re-loading.
    test_sizes = dict(new_size_small=(64, 48),
                      new_size_wide=(500, 250),
                      new_size_narrow=(250, 500))
    vm2 = VectorManager(None)
    vm2.load(save_file)
    for name, size in test_sizes.items():

        view2 = view.from_new_size(size)
        frame2 = (np.zeros((size[1], size[0], 3)) + COLORS_RGB[BKG]).astype(np.uint8)
        vm2.render(frame2, view2)
        
        if show:
            cv2.imshow(name, frame2)
            

    # check that the vectors are the same
    for v1, v2 in zip(vm._elements, vm2._elements):
        assert v1 == v2, f"vectors should be the same: {v1.get_data()} != {v2.get_data()}"

    # render the vectors from the loaded manager
    frame2 = (np.zeros((display_size[1], display_size[0], 3)) + COLORS_RGB[BKG]).astype(np.uint8)

    if show:
        cv2.imshow('test_vectors', frame)
        cv2.waitKey(0)

    return True


def test_board_view():
    """
    Create a bunch of points in [0, 100] x [0, 10], create a board view that fits them into a 640x480 window.
    Create a few bboxes that should be in the view and a few that should not then check them.
    """
    np.random.seed(0)
    size = (640, 480)
    points = np.random.rand(100*2).reshape((100, 2)) * np.array([100, 10])
    view = get_board_view(points, size, margin=0.025)

    visible_bboxes = [('points bbox', {'x': (0, 100), 'y': (0, 10)}),
                      ('big bbox', {'x': (-10, 120), 'y': (-1, 11)}),
                      ('small bbox', {'x': (2, 3), 'y': (3, 4)}),
                      ('tall bbox', {'x': (50, 60), 'y': (-4, 14)})]
    offscreen_bboxes = [('left bbox', {'x': (-10, -5), 'y': (0, 10)}),
                        ('right bbox', {'x': (110, 120), 'y': (0, 10)}),
                        ('top bbox', {'x': (0, 100), 'y': (220, 230)}),
                        ('bottom bbox', {'x': (0, 100), 'y': (-220, -210)})]
    for name, bbox in visible_bboxes:
        assert view.sees_bbox(bbox), f"{name} should be visible: {bbox} should be in {view.board_bbox}"

    for name, bbox in offscreen_bboxes:
        assert not view.sees_bbox(bbox), f"{name} should not be visible {bbox} should not be in {view.board_bbox}"
    print("test_vectors.py: All tests pass")


if __name__ == '__main__':
    test_board_view()
    test_vectors()
    print("test_vectors.py: All tests pass")
