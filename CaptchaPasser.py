import io
import time
from playwright.sync_api import sync_playwright, Route
from CaptchaCv2 import (get_track_list, qq_mark_pos)

distance = 0
is_reflashed_img = False
img = "bg.png"
retryTimes = 10


def handle_captcha(route: Route) -> None:
    response = route.fetch()
    if response.status == 200:
        buffer = response.body()
        # 下载指定规则url的验证码图片
        if "index=1" in response.url:
            is_reflashed_img = True
            with open(img, "wb") as f:
                f.write(buffer)
    route.continue_()


def dragbox_location():
    for i in range(5):
        dragbox_bounding = page.frame_locator("#tcaptcha_iframe").locator(
            "#tcaptcha_drag_thumb").bounding_box()
        if dragbox_bounding is not None and dragbox_bounding["x"] > 20:
            return dragbox_bounding
    return None


def drag_to_breach(move_distance):
    print('开始拖动滑块..')
    drag_box = dragbox_location()
    if drag_box is None:
        print('未获取到滑块位置,识别失败')
        return False
    page.mouse.move(drag_box["x"] + drag_box["width"] / 2,
                    drag_box["y"] + drag_box["height"] / 2)
    page.mouse.down()
    location_x = drag_box["x"]
    for i in move_distance:
        location_x += i
        page.mouse.move(location_x, drag_box["y"])
    page.mouse.up()
    if page.get_by_text("后重试") is not None or page.get_by_text("请控制拼图对齐缺口") is not None:
        print("识别成功")
        return True
    print('识别失败')
    return False


def calc_distance():
    for i in range(retryTimes):
        print(f"识别验证码距离中，当前等待轮数{i + 1}/{retryTimes}")
        try:
            res = qq_mark_pos(img)
            distance = res.x.values[0]
            if distance > 0:
                print(f"获取到缺口距离：{distance}")
                return distance
        except Exception as e:
            print(f"识别错误, 异常：{e}")


with sync_playwright() as p:
    # browser = p.chromium.launch(channel="msedge",proxy={"server": "http://{}".format(proxy)})
    browser = p.chromium.launch(channel="msedge", headless=False)
    iphone_12 = p.devices["iPhone 12"]
    context = browser.new_context(
        record_video_dir="videos/",
        **iphone_12,
    )
    page = context.new_page()
    # 下载指定规则的验证码图片
    page.route("**/t.captcha.qq.com/hycdn**", handle_captcha)
    page.route("**/t.captcha.qq.com/cap_union_new_getcapbysig**", handle_captcha)
    page.goto(
        "https://wap.showstart.com/pages/passport/login/login?redirect=%252Fpages%252FmyHome%252FmyHome")

    page.get_by_role("spinbutton").fill("14445104596")
    page.get_by_text("获取验证码").click()

    frame = page.wait_for_selector("#tcaptcha_iframe")
    print(frame.bounding_box())
    move_distance = None
    for i in range(retryTimes):
        print(f"滑块拖动逻辑开始，当前尝试轮数{i + 1}/{retryTimes}")

        # 验证码刷新 重新计算距离
        if is_reflashed_img or move_distance is None:
            distance = calc_distance()
            page.wait_for_timeout(200)

            true_distance = distance * 353 / 680
            move_distance = get_track_list(true_distance)
            print(f"获取到相对滑动距离{true_distance}, 模拟拖动列表{move_distance}")
            is_reflashed_img = False

        drag_result = drag_to_breach(move_distance)
        if drag_result:
            break

    page.wait_for_timeout(3000)
    print("识别结束，退出程序")
    # input("为方便调试，可启用此代码，避免浏览器关闭")
    browser.close()
