import math
from collections import namedtuple
from typing import List, Tuple, Union

Point = namedtuple("Point", ["x", "y"])


class ConvexPolygon:
    """
    Выпуклый многоугольник на плоскости.

    Требования к входным данным:
        - Вершины должны быть заданы в порядке обхода (по часовой или против часовой стрелки).
        - Все вершины должны быть различны, и их должно быть не менее трёх.
        - Многоугольник должен быть выпуклым.

    При нарушении этих условий при инициализации будет выброшено ValueError.
    """

    def __init__(self, vertices: List[Union[Point, Tuple[float, float]]]):
        if len(vertices) < 3:
            raise ValueError("Многоугольник должен иметь минимум 3 вершины")

        # Преобразуем всё в Point и float для единообразия
        self._vertices = tuple(
            Point(float(x), float(y)) for x, y in vertices
        )

        if not self._is_convex():
            raise ValueError(
                "Заданные вершины не образуют выпуклый многоугольник "
                "или заданы не в порядке обхода (по/против часовой стрелки)."
            )

        self._area = None
        self._perimeter = None
        self._bounding_box = None

    def _is_convex(self) -> bool:
        """Проверяет выпуклость при условии, что вершины заданы в порядке обхода."""
        n = len(self._vertices)
        if n < 3:
            return False

        # Найдём первый ненулевой поворот, чтобы определить направление
        first_sign = None
        for i in range(n):
            p1 = self._vertices[i]
            p2 = self._vertices[(i + 1) % n]
            p3 = self._vertices[(i + 2) % n]

            # Вектор p1->p2 и p2->p3
            dx1 = p2.x - p1.x
            dy1 = p2.y - p1.y
            dx2 = p3.x - p2.x
            dy2 = p3.y - p2.y

            # Псевдоскалярное (векторное) произведение: dx1*dy2 - dy1*dx2
            cross = dx1 * dy2 - dy1 * dx2

            if cross != 0:
                current_sign = cross > 0
                if first_sign is None:
                    first_sign = current_sign
                elif first_sign != current_sign:
                    return False
        # Если все повороты нулевые — все точки коллинеарны → не многоугольник
        return first_sign is not None

    @property
    def vertices(self) -> Tuple[Point, ...]:
        """Возвращает вершины в порядке обхода."""
        return self._vertices

    @property
    def area(self) -> float:
        if self._area is None:
            n = len(self._vertices)
            area = 0.0
            for i in range(n):
                p1 = self._vertices[i]
                p2 = self._vertices[(i + 1) % n]
                area += p1.x * p2.y - p2.x * p1.y
            self._area = abs(area) / 2.0
        return self._area

    @property
    def perimeter(self) -> float:
        if self._perimeter is None:
            n = len(self._vertices)
            perim = 0.0
            for i in range(n):
                p1 = self._vertices[i]
                p2 = self._vertices[(i + 1) % n]
                perim += math.hypot(p2.x - p1.x, p2.y - p1.y)
            self._perimeter = perim
        return self._perimeter

    @property
    def bounding_box(self) -> Tuple[float, float, float, float]:
        """(min_x, min_y, max_x, max_y)"""
        if self._bounding_box is None:
            xs = [v.x for v in self._vertices]
            ys = [v.y for v in self._vertices]
            self._bounding_box = (min(xs), min(ys), max(xs), max(ys))
        return self._bounding_box

    def contains_point(self, point: Union[Point, Tuple[float, float]]) -> bool:
        """
        Проверяет, лежит ли точка внутри или на границе многоугольника.
        Работает корректно только для выпуклых многоугольников с упорядоченными вершинами.
        """
        if not isinstance(point, Point):
            point = Point(float(point[0]), float(point[1]))
        px, py = point.x, point.y

        n = len(self._vertices)
        sign = None

        for i in range(n):
            a = self._vertices[i]
            b = self._vertices[(i + 1) % n]

            # Вектор ребра: b - a
            # Вектор от a к точке: (px - a.x, py - a.y)
            cross = (b.x - a.x) * (py - a.y) - (b.y - a.y) * (px - a.x)

            if cross != 0:
                current_sign = cross > 0
                if sign is None:
                    sign = current_sign
                elif sign != current_sign:
                    return False
        # Если все cross == 0 — точка на границе (вырожденный случай)
        return True

    def contains_polygon(self, other: 'ConvexPolygon') -> bool:
        """Проверяет, лежит ли весь другой выпуклый многоугольник внутри этого (включая границу)."""
        return all(self.contains_point(v) for v in other.vertices)

    def intersects(self, other: 'ConvexPolygon') -> bool:
        """Проверяет пересечение с другим выпуклым многоугольником с помощью SAT."""
        if not self._sat_check(self._vertices, other._vertices):
            return False
        if not self._sat_check(other._vertices, self._vertices):
            return False
        return True

    def _sat_check(self, poly1: Tuple[Point, ...], poly2: Tuple[Point, ...]) -> bool:
        """Проверяет отсутствие разделяющей оси между poly1 и poly2."""
        n = len(poly1)
        for i in range(n):
            a = poly1[i]
            b = poly1[(i + 1) % n]

            # Ребро
            edge_x = b.x - a.x
            edge_y = b.y - a.y

            # Перпендикуляр (ось проекции) — не нормализуем!
            axis_x = -edge_y
            axis_y = edge_x

            # Пропускаем вырожденные рёбра (длина 0)
            if axis_x == 0 and axis_y == 0:
                continue

            min1, max1 = self._project(poly1, axis_x, axis_y)
            min2, max2 = self._project(poly2, axis_x, axis_y)

            # Проверка на непересечение проекций
            if max1 < min2 or max2 < min1:
                return False
        return True

    @staticmethod
    def _project(vertices: Tuple[Point, ...], axis_x: float, axis_y: float) -> Tuple[float, float]:
        """Проекция вершин на ось (axis_x, axis_y)."""
        min_proj = max_proj = vertices[0].x * axis_x + vertices[0].y * axis_y
        for v in vertices[1:]:
            proj = v.x * axis_x + v.y * axis_y
            if proj < min_proj:
                min_proj = proj
            elif proj > max_proj:
                max_proj = proj
        return min_proj, max_proj

    def triangulation(self) -> List[Tuple[Point, Point, Point]]:
        """Возвращает список треугольников (каждый — кортеж из 3 Point)."""
        n = len(self._vertices)
        if n < 3:
            return []
        return [
            (self._vertices[0], self._vertices[i], self._vertices[i + 1])
            for i in range(1, n - 1)
        ]

    def __repr__(self):
        return f"ConvexPolygon({list(self._vertices)})"


# ============ ТЕСТЫ ============

if __name__ == "__main__":
    # Корректные выпуклые многоугольники (в порядке обхода!)
    try:
        poly1 = ConvexPolygon([(0, 0), (4, 0), (4, 4), (0, 4)])  # квадрат
        poly2 = ConvexPolygon([(1, 1), (3, 1), (3, 3), (1, 3)])  # внутренний квадрат
    except ValueError as e:
        print("Ошибка при создании:", e)
        exit(1)

    print("Многоугольник 1:", poly1.vertices)
    print("Многоугольник 2:", poly2.vertices)

    print("Площадь Многоугольника 1:", poly1.area)
    print("Площадь Многоугольника 2:", poly2.area)
    print("Периметр Многоугольника 1:", poly1.perimeter)
    print("Периметр Многоугольника 2:", poly2.perimeter)

    print("Триангуляция Многоугольника 1:", poly1.triangulation())
    print("Триангуляция Многоугольника 2:", poly2.triangulation())

    if poly1.contains_polygon(poly2):
        print("Многоугольник 2 полностью находится внутри Многоугольника 1")
    else:
        print("Многоугольник 2 НЕ находится внутри Многоугольника 1")

    if poly1.intersects(poly2):
        print("Многоугольники пересекаются")
    else:
        print("Многоугольники не пересекаются")

    # Тест точки
    print("Точка (2,2) внутри poly1?", poly1.contains_point((2, 2)))
    print("Точка (5,5) внутри poly1?", poly1.contains_point((5, 5)))
    print("Точка (0,0) внутри poly1?", poly1.contains_point((0, 0)))  # на границе