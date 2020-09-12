from heapq import heappush, heappop
from sys import maxsize

edges = {1: [2, 8, 9],
         2: [1, 10, 3],
         8: [1, 7, 12, 9],
         9: [1, 8, 12, 10],
         10: [2, 3, 4, 12, 11, 9],
         3: [2, 10, 4],
         4: [3, 10, 5, 11],
         5: [4, 6],
         11: [4, 6, 10],
         6: [5, 11, 13, 7],
         13: [6, 7, 12],
         7: [6, 13, 8],
         12: [8, 13, 9, 10]}


def neighbors(node):
    return edges[node]


# Represent each node as a list, ordering the elements so that a heap of nodes
# is ordered by f = g + h, with h as a first, greedy tie-breaker and num as a
# second, definite tie-breaker. Store the redundant g for fast and accurate
# calculations.

F, H, NUM, G, POS, OPEN, VALID, PARENT = range(8)


def astar(start_pos, neighbors, goal, start_g, cost, heuristic, limit=maxsize,
          debug=None):
    """Find the shortest path from start to goal.
    Arguments:
      start_pos      - The starting position.
      neighbors(pos) - A function returning all neighbor positions of the given
                       position.
      goal(pos)      - A function returning true given a goal position, false
                       otherwise.
      start_g        - The starting cost.
      cost(a, b)     - A function returning the cost for moving from one
                       position to another.
      heuristic(pos) - A function returning an estimate of the total cost
                       remaining for reaching goal from the given position.
                       Overestimates can yield suboptimal paths.
      limit          - The maximum number of positions to search.
      debug(nodes)   - This function will be called with a dictionary of all
                       nodes.
    The function returns the best path found. The returned path excludes the
    starting position.
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

                # We have found a new node.
                neighbor_h = heuristic(neighbor_pos)
                neighbor = [neighbor_g + neighbor_h, neighbor_h, next(nums),
                            neighbor_g, neighbor_pos, True, True, current[POS]]
                nodes[neighbor_pos] = neighbor
                heappush(heap, neighbor)
                if neighbor_h < best[H]:
                    # We are approaching the goal.
                    best = neighbor

            elif neighbor_g < neighbor[G]:

                # We have found a better path to the neighbor.
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
