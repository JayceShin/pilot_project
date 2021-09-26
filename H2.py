from collections import deque


def solution(n, a, cards):
    ans = 0
    queue = deque()

    for i in range(n):

        if len(cards) == i:
            if i == a:
                queue.append(chr(0))
            break

        if i != a:
            queue.append(cards[i])
        else:
            queue.append(chr(0))
            queue.append(cards[i])

    match = int(len(queue)/2)
    nowGame = 0
    before = None

    while queue:

        if len(queue) == 1:
            break

        if match == nowGame:
            if len(queue) % 2 != 0:
                temp = queue.popleft()
                queue.append(temp)

            nowGame = 0
            match = int(len(queue)/2)
            continue

        nowCard = queue.popleft()
        nextCard = queue.popleft()

        winner = compete(nowCard, nextCard, before)

        if len(winner) == 1:
            queue.append(winner)
        elif winner[1] is not None:
            before = winner[1]
            queue.append(chr(0))
            ans = ans + winner[0]

        nowGame = nowGame + 1

    return ans


def compete(cBefore, cNext, bInfo):

    result = abs(ord(cBefore)-ord(cNext))

    if result == 0:

        if cBefore == "R":
            win = "P"
        elif cBefore == "S":
            win = "R"
        else:
            win = "S"

        return win, None

    elif result == 1:
        return "R"
    elif result == 2:
        return "P"
    elif result == 3:
        return "S"
    else:

        if bInfo is None:
            temp = compete(chr(result), chr(result), None)[0]
            ans = 0
        else:
            temp = compete(max(cBefore, cNext), bInfo, None)
            if temp != bInfo:
                ans = 1

        return ans, temp


if __name__ == '__main__':
    people = 6
    me = 2
    cardInfo = "PPSRP"

    # R - S = 1/ -1 -> R = -1
    # R - P = 2/ -2 -> P = -2
    # P - S = 3/ -3 -> S = 3

    print(solution(people, me, cardInfo))
