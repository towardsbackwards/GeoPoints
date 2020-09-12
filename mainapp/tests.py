from heapq import heappush, heappop
from sys import maxsize


# Represent each node as a list, ordering the elements so that a heap of nodes
# is ordered by f = g + h, with h as a first, greedy tie-breaker and num as a
# second, definite tie-breaker. Store the redundant g for fast and accurate
# calculations.




def astar(start_pos, neighbors, goal, start_g, cost, heuristic, limit=maxsize,
          debug=None):
    F, H, NUM, G, POS, OPEN, VALID, PARENT = range(8)
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
      debug(nodes)   - This function will be called with a dictionary of all
                       nodes.
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
        if goal(current[POS]):
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
