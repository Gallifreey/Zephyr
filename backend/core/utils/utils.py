FORMAT_LEFT_BRACE = '{'
FORMAT_RIGHT_BRACE = '}'
FORMAT_ENTER = '\n'
FORMAT_BIGGER = '＞'
FORMAT_SMALLER = '＜'
COLOR_PICKER = ['lightgrey', 'lightblue2', 'cyan', 'lightgreen', 'lightyellow', 'lightcyan', 'lightpink']


def check_in_region(target, points):
    px, py = target
    is_in = False
    for i, corner in enumerate(points):
        next_i = i + 1 if i + 1 < len(points) else 0
        x1, y1 = corner
        x2, y2 = points[next_i]
        if (x1 == px and y1 == py) or (x2 == px and y2 == py):
            is_in = True
            break
        if min(y1, y2) < py <= max(y1, y2):
            x = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if x == px:
                is_in = True
                break
            elif x > px:
                is_in = not is_in
    return is_in
