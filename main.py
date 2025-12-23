import math


class ConPolygon:
    def __init__(self, vertices):
        if len(vertices) < 3:
            raise ValueError("Многоугольник должен иметь минимум 3 вершины")

        self._vertices = tuple((float(x), float(y)) for x, y in vertices)


        if len(self._vertices) != len(set(self._vertices)):
            raise ValueError("Вершины не должны повторяться")

        if not self._is_con():
            raise ValueError("Многоугольник не является выпуклым")

        self.vertices = self._sort_vertices(vertices)
        self._area = None
        self._perimeter = None
        self._bounding_box = None

    def _sort_vertices(self, vertices):
        center_x = sum(x for x, y in vertices) / len(vertices)
        center_y = sum(y for x, y in vertices) / len(vertices)
        return sorted(vertices, key=lambda p: math.atan2(p[1] - center_y, p[0] - center_x))

    def _is_con(self):
        n = len(self._vertices)
        if n < 3:
            return False

        first_nonzero_sign = 0
        for i in range(n):
            x1, y1 = self._vertices[i]
            x2, y2 = self._vertices[(i + 1) % n]
            x3, y3 = self._vertices[(i + 2) % n]

            cross_product = (x2 - x1) * (y3 - y2) - (y2 - y1) * (x3 - x2)


            if abs(cross_product) < 1e-10:
                continue


            if first_nonzero_sign == 0:
                first_nonzero_sign = 1 if cross_product > 0 else -1
            else:

                current_sign = 1 if cross_product > 0 else -1
                if current_sign != first_nonzero_sign:
                    return False
        if first_nonzero_sign == 0:
            return False

        #проверка на самопересечение
        return not self._has_self_intersection()

    def _has_self_intersection(self):
        """Проверка на самопересечение сторон"""
        n = len(self._vertices)

        for i in range(n):
            for j in range(i + 1, n):

                if j == (i + 1) % n or i == (j + 1) % n:
                    continue

                if self._segments_intersect(
                        self._vertices[i], self._vertices[(i + 1) % n],
                        self._vertices[j], self._vertices[(j + 1) % n]
                ):
                    return True
        return False

    def _segments_intersect(self, p1, p2, p3, p4):

        def orientation(a, b, c):
            val = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
            if val > 0:
                return 1
            elif val < 0:
                return -1
            return 0

        def on_segment(a, b, c):
            return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and
                    min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))

        o1 = orientation(p1, p2, p3)
        o2 = orientation(p1, p2, p4)
        o3 = orientation(p3, p4, p1)
        o4 = orientation(p3, p4, p2)

        if o1 != o2 and o3 != o4:
            return True

        #коллинеарность
        if o1 == 0 and on_segment(p1, p2, p3):
            return True
        if o2 == 0 and on_segment(p1, p2, p4):
            return True
        if o3 == 0 and on_segment(p3, p4, p1):
            return True
        if o4 == 0 and on_segment(p3, p4, p2):
            return True

        return False


    def triangulation(self):
        return [
            [self.vertices[0], self.vertices[i], self.vertices[i + 1]]
            for i in range(1, len(self.vertices) - 1)
        ]

    @property
    def area(self):
        if self._area is None:
            n = len(self._vertices)
            area = 0
            for i in range(n):
                x1, y1 = self._vertices[i]
                x2, y2 = self._vertices[(i + 1) % n]
                area += x1 * y2 - x2 * y1
            self._area = abs(area) / 2
        return self._area

    @property
    def perimeter(self):
        if self._perimeter is None:
            n = len(self._vertices)
            perimeter = 0
            for i in range(n):
                x1, y1 = self._vertices[i]
                x2, y2 = self._vertices[(i + 1) % n]
                perimeter += math.hypot(x2 - x1, y2 - y1)
            self._perimeter = perimeter
        return self._perimeter

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            xs = [v[0] for v in self._vertices]
            ys = [v[1] for v in self._vertices]
            self._bounding_box = (min(xs), min(ys), max(xs), max(ys))
        return self._bounding_box

    def contains_point(self, point):
        min_x, min_y, max_x, max_y = self.bounding_box
        px, py = point
        if not (min_x <= px <= max_x and min_y <= py <= max_y):
            return False
        return True

    def contains_polygon(self, other):
        min1_x, min1_y, max1_x, max1_y = self.bounding_box
        min2_x, min2_y, max2_x, max2_y = other.bounding_box

        if min2_x < min1_x or max2_x > max1_x or min2_y < min1_y or max2_y > max1_y:
            return False

        return all(self.contains_point(vertex) for vertex in other.vertices)

    def intersects(self, other):
        min1_x, min1_y, max1_x, max1_y = self.bounding_box
        min2_x, min2_y, max2_x, max2_y = other.bounding_box

        if max1_x < min2_x or max2_x < min1_x or max1_y < min2_y or max2_y < min1_y:
            return False

        if not self._check_axes(self, other):
            return False

        if not self._check_axes(other, self):
            return False

        return True

    def _check_axes(self, poly1, poly2):
        n = len(poly1.vertices)

        for i in range(n):
            x1, y1 = poly1.vertices[i]
            x2, y2 = poly1.vertices[(i + 1) % n]
            edge_x = x2 - x1
            edge_y = y2 - y1
            axis_x = -edge_y
            axis_y = edge_x
            length = math.sqrt(axis_x ** 2 + axis_y ** 2)
            if length == 0:
                continue

            axis_x /= length
            axis_y /= length
            min1, max1 = self._project_polygon(poly1.vertices, axis_x, axis_y)
            min2, max2 = self._project_polygon(poly2.vertices, axis_x, axis_y)
            if max1 < min2 or max2 < min1:
                return False

        return True

    def _project_polygon(self, vertices, axis_x, axis_y):
        min_proj = float('inf')
        max_proj = float('-inf')

        for x, y in vertices:
            projection = x * axis_x + y * axis_y
            if projection < min_proj:
                min_proj = projection
            if projection > max_proj:
                max_proj = projection

        return min_proj, max_proj



try:
    convex_poly = ConPolygon([(0, 0), (3, 0), (3, 3), (0, 3)])
    print("Выпуклый многоугольник создан успешно")
    print("Вершины:", convex_poly.vertices)
    print("Площадь:", convex_poly.area)
except ValueError as e:
    print("Ошибка:", e)

try:
    # Пример невыпуклого самопересекающийся
    non_convex = ConPolygon([(0, 0), (3, 3), (3, 0), (0, 3)])
    print("Самопересекающийся многоугольник создан")
except ValueError as e:
    print("Ошибка:", e)

try:
    # Пример невыпуклого вогнутый
    concave_poly = ConPolygon([(0, 0), (4, 0), (4, 4), (1, 1), (0, 4)])
    print("Вогнутый многоугольник создан успешно (не должно быть!)")
except ValueError as e:
    print("Ошибка (ожидаемая):", e)

test_poly1 = ConPolygon([(0, 0), (2, 0), (3, 2), (1, 4), (-1, 2)])
test_poly2 = ConPolygon([(1, 1), (3, 1), (5, 5), (1, 5)])

print("\nМногоугольник 1:", test_poly1.vertices)
print("Многоугольник 2:", test_poly2.vertices)

print("Площадь Многоугольник 1:", test_poly1.area)
print("Площадь Многоугольник 2:", test_poly2.area)
print("Периметр Многоугольник 1:", test_poly1.perimeter)
print("Периметр Многоугольник 2:", test_poly2.perimeter)
print("Триангуляция Многоугольник 1:", test_poly1.triangulation())
print("Триангуляция Многоугольник 2:", test_poly2.triangulation())

if test_poly1.contains_polygon(test_poly2):
    print("Многоугольник 1 находится в многоугольнике 2")
else:
    print("Многоугольник 1 не находится в многоугольнике 2")

if test_poly1.intersects(test_poly2):
    print("Многоугольники пересекаются")
else:
    print("Многоугольники не пересекаются")
