from heapq import heappush, heappop
from sys import maxsize
import collections

# инициализация ключей с условными значениями
F, H, NUM, G, POS, OPEN, VALID, PARENT = range(8)


def min_length(start_point, end_point, line_model, point_model):
    """Функция поиска кратчайшего пути между точками a & b
    Возвращает список точек (узлов), по которым был составлен маршрут
    (используя алгоритм A*), и его общую длину
    Аргументы:
            start_point     - id стартовой точки (int)
            end_point       - id конечной точки (int)
            point_model     - Django-модель точки
            point_model     - Django-модель линии (с FK к point model - from_point & to_point)"""
    depend_nodes = collections.defaultdict(list)
    for line in line_model.objects.all():
        # формируем словарь узел (int) - связи (list)
        n_from = line.from_point.id
        n_to = line.to_point.id
        depend_nodes[n_from].append(n_to)
        depend_nodes[n_to].append(n_from)

    def open_neighbors(node):
        """Функция, возвращающая всех соседей точки (pos): function > returns list"""
        return depend_nodes[node]

    def distance_eval(a, b):
        """Расчет дистанции между a & b в километрах"""
        return point_model.objects.get(id=a).geom.distance(point_model.objects.get(id=b).geom) * 100

    def heuristic_eval(pos):
        """Расчет эвристики. Конечная точка эвристики = конечная точка пути.
        Функция сообщает, насколько мы в данный момент близки к цели"""
        # расчет, в какую сторону стоит сделать следующий шаг?
        return point_model.objects.get(id=pos).geom.distance(point_model.objects.get(id=end_point).geom) * 100

    def path_length(path_list):
        """Функция, возвращающая общую длину пути по рассчитаным astar точкам"""
        distance = 0
        for i in range(len(path_list)):
            if len(path_list[i:i + 2]) == 2:
                section = path_list[i:i + 2]
                distance += distance_eval(section[0], section[1])
        return distance

    def a_star(start_pos, neighbors, goal_point, start_g, cost, heuristic, limit=maxsize):
        """Поиск кратчайшего пути от точки до цели.
        Функция возвращает наиболее короткий маршрут от точки start_pos до целевой точки, включая стартовую позицию.
        Аргументы:
          start_pos      - Стартовая точка: int
          neighbors(pos) - Функция, возвращающая всех соседей точки (pos): function > returns list
          goal(pos)      - Функция, возвращающая True при достижении цели и False в противном случае
          start_g        - Начальная стоимость: float
          cost(a, b)     - Функция, возвращающая стоимость перехода из точки a в точку b: float
          heuristic(pos) - Функция, возвращающая остаточную стоимость достижения цели с текущей позиции
                           Завышенные оценки могут привести к неоптимальным путям.
          limit          - Максимальное число позиций для поиска
        """

        # Создание стартового узла
        nums = iter(range(maxsize))  # создание итератора для "бесконечного" осуществления следующего шага
        start_h = heuristic(start_pos)
        start = [start_g + start_h, start_h, next(nums), start_g, start_pos, True,
                 True, None]
        # Отслеживание всех просмотренных узлов
        nodes = {start_pos: start}

        # Содержанит кучу узлов
        heap = [start]

        # Отслеживание лучшего найденного пути
        best = start
        # Пока в куче есть узлы
        while heap:
            # Берём следующий узел и удаляем его из кучи
            current = heappop(heap)
            # Устанавливаем, что соседи узла не раскрыты ???
            current[OPEN] = False

            # Мы достигли цели?
            if current[POS] == goal_point:
                best = current
                break
            # Раскрываем узел, посещая соседские
            for neighbor_pos in neighbors(current[POS]):
                neighbor_g = current[G] + cost(current[POS], neighbor_pos)
                neighbor = nodes.get(neighbor_pos)
                if neighbor is None:

                    # Лимит поиска
                    if len(nodes) >= limit:
                        continue

                    # Мы нашли новый узел
                    neighbor_h = heuristic(neighbor_pos)
                    neighbor = [neighbor_g + neighbor_h, neighbor_h, next(nums),
                                neighbor_g, neighbor_pos, True, True, current[POS]]
                    nodes[neighbor_pos] = neighbor
                    heappush(heap, neighbor)
                    if neighbor_h < best[H]:
                        # We are approaching the goal.
                        best = neighbor

                elif neighbor_g < neighbor[G]:

                    # Мы нашли более выгодный путь к соседней точке
                    if neighbor[OPEN]:

                        # Соседний узел уже раскрыт. Найти и обновить его в куче
                        # было бы операцией линейной сложности.
                        # Вместо этого мы помечаем соседа как VALID=False и
                        # делаем его обновленную копию.

                        neighbor[VALID] = False
                        nodes[neighbor_pos] = neighbor = neighbor[:]
                        neighbor[F] = neighbor_g + neighbor[H]
                        neighbor[NUM] = next(nums)
                        neighbor[G] = neighbor_g
                        neighbor[VALID] = True
                        neighbor[PARENT] = current[POS]
                        heappush(heap, neighbor)

                    else:

                        # Открываем соседний узел заново (его копию)
                        neighbor[F] = neighbor_g + neighbor[H]
                        neighbor[G] = neighbor_g
                        neighbor[PARENT] = current[POS]
                        neighbor[OPEN] = True
                        heappush(heap, neighbor)

            # Discard leading invalid nodes from the heap.
            while heap and not heap[0][VALID]:
                heappop(heap)

        # Return the best path as a list.
        path = []
        current = best
        while current[PARENT] is not None:
            path.append(current[POS])
            current = nodes[current[PARENT]]
        path.append(start_pos)
        path.reverse()
        return path

    final_path = a_star(start_point, open_neighbors, end_point, 0, distance_eval, heuristic_eval)
    # geojson?
    path_in_km = round(path_length(final_path), 2)
    result = {'start_point': start_point, 'end_point': end_point, 'path': final_path, 'path_in_km': path_in_km}
    return result
