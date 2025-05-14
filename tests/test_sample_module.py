from src.sample_module import add, subtract


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_sample_function():
    assert subtract(5, 3) == 2
    assert subtract(0, 1) == -1
