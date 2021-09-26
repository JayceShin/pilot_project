from collections import deque


dx = [-2, -1, 2, 1, 2, 1, -2, -1]
dy = [1, 2, 1, 2, -1, -2, -1, -2]


def solution(n, sr, sc, er, ec):
    map = [[0]*n for i in range(n)]
    check = [[False] * n for i in range(n)]

    q = deque()
    q.append([sr, sc])
    check[sr][sc] = True

    while q:
        x, y = q.popleft()
        if x == er and y == ec:
            break
        for i in range(8):
            newX = x + dx[i]
            newY = y + dy[i]
            if 0 <= newX < n and 0 <= newY < n and check[newX][newY] is False:
                q.append([newX, newY])
                check[newX][newY] = True
                map[newX][newY] = map[x][y] + 1

    if map[er][ec] == 0:
        ans = -1
    else:
        ans = map[er][ec]

    return ans


if __name__ == '__main__':
    num = 10
    startRow = 0
    startCol = 0
    endRow = 0
    endCol = 2
    print(solution(num, startRow, startCol, endRow, endCol))
