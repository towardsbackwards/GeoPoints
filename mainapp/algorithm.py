from heapq import heappush, heappop
from sys import maxsize
import collections
from mainapp.models import Point, Line

F, H, NUM, G, POS, OPEN, VALID, PARENT = range(8)


def min_length(start_point, end_point):
    """Функция поиска кратчайшего пути между точками a & b
    Возвращает список точек (узлов), по которым был составлен маршрут
    (используя алгоритм A*), и его общую длину"""
    depend_nodes = collections.defaultdict(list)
    for line in Line.objects.all():
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
        return Point.objects.get(id=a).geom.distance(Point.objects.get(id=b).geom) * 100

    def heuristic_eval(pos):
        """Расчет эвристики конечная точка эвристики = конечная точка пути"""
        return Point.objects.get(id=pos).geom.distance(Point.objects.get(id=end_point).geom) * 100

    def path_in_km(path_list):
        """Функция, возвращающая общую длину пути по рассчитаным astar точкам"""
        distance = 0
        for i in range(len(path_list)):
            if len(path[i:i + 2]) == 2:
                section = path_list[i:i + 2]
                distance += distance_eval(section[0], section[1])
        return distance

    def astar(start_pos, neighbors, goal_point, start_g, cost, heuristic, limit=maxsize,
              debug=None):
        """Поиск кратчайшего пути от точки до цели.
        Аргументы:
          start_pos      - Стартовая точка: int
          neighbors(pos) - Функция, возвращающая всех соседей точки (pos): function > returns list
          goal(pos)      - Функция, возвращающая True при достижении цели и False в противном случае
          start_g        - Начальная стоимость: float
          cost(a, b)     - Функция, возвращающая стоимость перехода из точки a в точку b: float
          heuristic(pos) - A function returning an estimate of the total cost
                           remaining for reaching goal from the given position.
                           Overestimates can yield suboptimal paths.
          limit          - Максимальное число позиций для поиска
        Функция возвращает наиболее короткикй маршрут от точки start_pos до целевой точки, включая стартовую позицию.
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

                    # Limit the search.
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

                        # The neighbor is already open. Finding and updating it
                        # in the heap would be a linear complexity operation.
                        # Instead we mark the neighbor as invalid and make an
                        # updated copy of it.

                        neighbor[VALID] = False
                        nodes[neighbor_pos] = neighbor = neighbor[:]
                        neighbor[F] = neighbor_g + neighbor[H]
                        neighbor[NUM] = next(nums)
                        neighbor[G] = neighbor_g
                        neighbor[VALID] = True
                        neighbor[PARENT] = current[POS]
                        heappush(heap, neighbor)

                    else:

                        # Reopen the neighbor.
                        neighbor[F] = neighbor_g + neighbor[H]
                        neighbor[G] = neighbor_g
                        neighbor[PARENT] = current[POS]
                        neighbor[OPEN] = True
                        heappush(heap, neighbor)

            # Discard leading invalid nodes from the heap.
            while heap and not heap[0][VALID]:
                heappop(heap)

        if debug is not None:
            # Pass the dictionary of nodes to the caller.
            debug(nodes)

        # Return the best path as a list.
        path = []
        current = best
        while current[PARENT] is not None:
            path.append(current[POS])
            current = nodes[current[PARENT]]
        path.append(start_pos)
        path.reverse()
        return path

    path = astar(start_point, open_neighbors, end_point, 0, distance_eval, heuristic_eval)
    # geojson?
    return f'Кратчайший путь от {start_point} до {end_point} проходит через ' \
           f'точки: {path}, общая длина этого пути: {path_in_km(path)} км'
