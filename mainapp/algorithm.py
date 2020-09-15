from heapq import heappush, heappop
from sys import maxsize
import collections

# инициализация именований индексов для значений узлов
# Представление каждого узла как list, упорядочивая их в куче по по формуле
# f = стартовая стоимость (g) + значение эвристики для текущего узла (h)
# Чем меньше это значение - тем приоритетней точка (узел)
F, H, NUM, G, POS, OPEN, VALID, PARENT = range(8)


def best_path_by(start_point, end_point, line_model, point_model, eval_type='by_distance'):
    """Функция поиска кратчайшего пути между точками a & b
    Возвращает список точек (узлов), по которым был составлен маршрут
    (используя алгоритм A*), и его общую длину
    Аргументы:
            start_point     - id стартовой точки (int)
            end_point       - id конечной точки (int)
            point_model     - Django-модель точки
            point_model     - Django-модель линии (с FK к point model - from_point & to_point)
            eval            - Способ вычисления (by_distance - поиск пути по кратчайшему расстоянию;
                                                by_score - по минимальному количеству баллов)"""
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

    def score_eval(a, b):
        """Расчет стоимости между a & b в баллах"""
        return point_model.objects.get(id=a).score + point_model.objects.get(id=b).score

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
        # Создание стартового узла
        nums = iter(range(maxsize))  # обеспечиваем функцию "бесконечным" запасом шагов
        start_h = heuristic(start_pos)
        start_node = [start_cost + start_h, start_h, next(nums), start_cost, start_pos, True,
                      True, None]
        # Отслеживание всех просмотренных узлов
        closed_nodes = {start_pos: start_node}
        # Содержит кучу узлов
        open_heap = [start_node]
        # Установка лучшего найденного пути
        best = start_node
        # Пока в куче есть узлы
        while open_heap:
            current = heappop(open_heap)  # ДОСТАЛИ УЗЕЛ С НАИМЕНЬШЕЙ СТОИМОСТЬЮ ИЗ ОТКРЫТЫХ
            current[OPEN] = False  # УСТАНОВИЛИ, ЧТО УЗЕЛ ПРОСМОТРЕН
            # КОНЕЦ, ЕСЛИ УЗЕЛ СОВПАДАЕТ С ФИНИШЕМ
            if current[POS] == goal_point:
                best = current
                break
            # РАСКРЫВАЕМ СОСЕДНИЕ УЗЛЫ, КОТОРЫЕ НЕ ЯВЛЯЮТСЯ ЗАКРЫТЫМИ ([OPEN] = True)
            for neighbor_pos in neighbors(current[POS]):
                new_neighbor_g = current[G] + cost(current[POS], neighbor_pos)  # полная стоимость до neighbor_pos
                neighbor = closed_nodes.get(neighbor_pos)  # берем соседа из списка просмотренных
                if neighbor is None:  # если этот сосед ещё не был просмотрен
                    # Лимит поиска
                    if len(closed_nodes) >= limit:
                        continue
                    # Зашли в следующий по порядку соседний узел
                    # присвоили ему значения и вставили в кучу просмотренных
                    neighbor_h = heuristic(neighbor_pos)
                    neighbor = [new_neighbor_g + neighbor_h, neighbor_h, next(nums),
                                new_neighbor_g, neighbor_pos, True, True, current[POS]]
                    closed_nodes[neighbor_pos] = neighbor
                    heappush(open_heap, neighbor)
                    if neighbor_h < best[H]:
                        best = neighbor  # Эвристика нового узла меньше. Мы приближаемся к цели.
                #  Если новая суммарная стоимость neighbor_pos меньше стоимости
                elif new_neighbor_g < neighbor[G]:  # 1-2-10 < 1-9-10
                    # Мы нашли более выгодный путь к соседней точке, чем просмотренный ранее
                    if neighbor[OPEN]:
                        # Соседний узел уже раскрыт. Найти и обновить его в куче
                        # было бы операцией линейной сложности.
                        # Вместо этого мы помечаем соседа как VALID=False и
                        # делаем его обновленную копию.
                        neighbor[VALID] = False
                        closed_nodes[neighbor_pos] = neighbor = neighbor[:]
                        neighbor[F] = new_neighbor_g + neighbor[H]
                        neighbor[NUM] = next(nums)
                        neighbor[G] = new_neighbor_g
                        neighbor[VALID] = True
                        neighbor[PARENT] = current[POS]
                        heappush(open_heap, neighbor)
                    else:
                        # Открываем соседей узла заново (его копию)
                        neighbor[F] = new_neighbor_g + neighbor[H]
                        neighbor[G] = new_neighbor_g
                        neighbor[PARENT] = current[POS]
                        neighbor[OPEN] = True
                        heappush(open_heap, neighbor)
            # Убираем из верхушки кучи узлы, помеченные невалидными
            while open_heap and not open_heap[0][VALID]:
                heappop(open_heap)
        # Возврат наилучшего пути в виде list
        path = []
        current = best
        while current[PARENT] is not None:
            path.append(current[POS])
            current = closed_nodes[current[PARENT]]
        path.append(start_pos)
        path.reverse()
        return path

    final_path = a_star(start_point, open_neighbors, end_point, 0, distance_eval, heuristic_eval)
    final_score_path = a_star(start_point, open_neighbors, end_point, 0, score_eval, heuristic_eval)
    # geojson?
    path_in_km = round(path_length(final_path), 2)
    path_in_score_points = round(path_score(final_path), 2)
    result_by_distance = {'start_point': start_point, 'end_point': end_point,
                          'path': final_path, 'path_in_km': path_in_km}
    result_by_score = {'start_point': start_point, 'end_point': end_point,
                       'path': final_score_path, 'path_in_score_points': path_in_score_points}
    if eval == 'by_distance':
        return result_by_distance
    elif eval == 'by_score':
        return result_by_score
