from heapq import heappush, heappop
from sys import maxsize
import collections

# инициализация именований индексов для значений узлов
# Представление каждого узла как list, упорядочивая их в куче по по формуле
# F = стартовая стоимость (G) + значение эвристики для текущего узла (H)
# Чем меньше это значение - тем приоритетней точка (узел)
# Узлы в heap упорядочены по значению F. В случае конфликта
# одинаковых значений F упорядочивание будет определено по NUM
# т.к. в куче кортежи сравниваются поэлементно слева направо.
F, H, NUM, G, POS, OPEN, VALID, PARENT = range(8)


def best_path_by(start_point, end_point, line_model, point_model, eval_type='by_distance'):
    """Функция поиска кратчайшего пути между точками a & b
    Возвращает список точек (узлов), по которым был составлен маршрут
    (используя алгоритм A*), и его общую длину
    Аргументы:
            start_point     - id стартовой точки (int)
            end_point       - id конечной точки (int)
            point_model     - Django-модель точки
            line_model     - Django-модель линии (с FK к point model - from_point & to_point)
            eval            - Способ вычисления (by_distance - поиск пути по кратчайшему расстоянию;
                                                by_score - по минимальному количеству баллов)"""
    depend_nodes = collections.defaultdict(list)
    for line in line_model.objects.all():
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

    def score_eval(a, b):
        """Расчет стоимости между a & b в баллах"""
        return point_model.objects.get(id=a).score + point_model.objects.get(id=b).score

    def heuristic_eval(pos):
        """Расчет эвристики. Конечная точка эвристики = конечная точка пути.
        Функция сообщает, насколько мы в данный момент близки к цели"""
        return point_model.objects.get(id=pos).geom.distance(point_model.objects.get(id=end_point).geom) * 100

    def path_length(path_list):
        """Функция, возвращающая общую длину пути по рассчитаным astar точкам"""
        distance = 0
        for i in range(len(path_list)):
            if len(path_list[i:i + 2]) == 2:
                section = path_list[i:i + 2]
                distance += distance_eval(section[0], section[1])
        return distance

    def path_score(path_score_list):
        """Функция, возвращающая общую score-стоимость пути по рассчитаным astar точкам"""
        total_score = 0
        for point in path_score_list:
            total_score += point_model.objects.get(id=point).score
        return total_score

    def a_star(start_pos, neighbors, goal_point, start_cost, cost, heuristic, limit=maxsize):
        """Поиск кратчайшего пути от точки до цели.
        Функция возвращает наиболее короткий маршрут от точки start_pos до целевой точки, включая стартовую позицию.
        Аргументы:
          start_pos      - Стартовая точка: int
          neighbors(pos) - Функция, возвращающая всех соседей точки (pos): function > returns list
          goal(pos)      - Функция, возвращающая True при достижении цели и False в противном случае
          start_cost        - Начальная стоимость: float
          cost(a, b)     - Функция, возвращающая стоимость перехода из точки a в точку b: float
          heuristic(pos) - Функция, возвращающая остаточную стоимость достижения цели с текущей позиции
                           Завышенные оценки могут привести к неоптимальным путям.
          limit          - Максимальное число позиций для поиска
        """
        nums = iter(range(maxsize))
        start_h = heuristic(start_pos)
        start_node = [start_cost + start_h, start_h, next(nums), start_cost, start_pos, True,
                      True, None]
        watched_nodes = {start_pos: start_node}
        nodes_heap = [start_node]
        best = start_node
        while nodes_heap:
            current = heappop(nodes_heap)  # получаем узел с минимальной стоимостью
                                          # (вначале это будет start_node), одновременно убирая его из nodes_heap
            current[OPEN] = False         # делаем узел закрытым
            if current[POS] == goal_point:
                best = current
                break
            for i in neighbors(current[POS]):
                new_neighbor_g = current[G] + cost(current[POS], i)  # полная стоимость этого соседа
                neighbor = watched_nodes.get(i)
                if neighbor is None:  # если мы смотрим этого соседа впервые (проверка для экономии ресурсов)
                    if len(watched_nodes) >= limit:
                        continue  # на случай достижения лимита 9223372036854775807 в куче продолжаем цикл
                    neighbor_h = heuristic(i)   # считаем эвристику для этого соседа
                    neighbor = [new_neighbor_g + neighbor_h, neighbor_h, next(nums),
                                new_neighbor_g, i, True, True, current[POS]]
                    watched_nodes[i] = neighbor    # добавляем посчитанный узел в просмотренные
                    heappush(nodes_heap, neighbor)  # как открытый (i = номер узла в БД)
                    if neighbor_h < best[H]:
                        best = neighbor  # Эвристика нового узла меньше. Обозначили его ближайшим к цели на текущий момент.
                elif new_neighbor_g < neighbor[G]:  # если стоимость до ранее просмотренного узла была больше, чем сейчас
                    if neighbor[OPEN]:  # соседний узел открыт - его соседи не раскрыты
                        neighbor[VALID] = False  # бракуем ранее просмотренный узел - FALSE
                        watched_nodes[i] = neighbor = neighbor[:]  # взяли копию узла из кучи как neighbor
                        #  обновляем значения узла на текущие и кладем в очередь
                        neighbor[F] = new_neighbor_g + neighbor[H]
                        neighbor[NUM] = next(nums)
                        neighbor[G] = new_neighbor_g
                        neighbor[VALID] = True
                        neighbor[PARENT] = current[POS]
                        heappush(nodes_heap, neighbor)
                    else:  # соседний узел закрыт - меняем его родителя, F и G и кладем в очередь
                        neighbor[F] = new_neighbor_g + neighbor[H]
                        neighbor[G] = new_neighbor_g
                        neighbor[PARENT] = current[POS]
                        neighbor[OPEN] = True
                        heappush(nodes_heap, neighbor)
            while nodes_heap and not nodes_heap[0][VALID]:  # удаляем невалидные лидирующие узлы
                heappop(nodes_heap)
        path = []
        # восстанавливаем путь от конечного узла до начального (current - конечный узел)
        current = best
        while current[PARENT] is not None:
            path.append(current[POS])
            current = watched_nodes[current[PARENT]]
        path.append(start_pos)
        path.reverse()
        return path

    if eval_type == 'by_distance':
        final_path = a_star(start_point, open_neighbors, end_point, 0, distance_eval, heuristic_eval)
        path_in_km = round(path_length(final_path), 2)
        result_by_distance = {'start_point': start_point, 'end_point': end_point,
                              'path': final_path, 'path_in_km': path_in_km}
        return result_by_distance

    elif eval_type == 'by_score':
        final_score_path = a_star(start_point, open_neighbors, end_point, 0, score_eval, heuristic_eval)
        path_in_score_points = round(path_score(final_score_path), 2)
        result_by_score = {'start_point': start_point, 'end_point': end_point,
                           'path': final_score_path, 'path_in_score_points': path_in_score_points}
        return result_by_score
