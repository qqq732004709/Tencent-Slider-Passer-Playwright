import io
import time
from playwright.sync_api import sync_playwright, Route
from CaptchaCv2 import (get_track_list, qq_mark_pos)

distance = 0
img = "bg.png"

def handle_captcha(route: Route) -> None:
    response = route.fetch()
    if response.status == 200:
        buffer = response.body()
        # 下载指定规则url的验证码图片
        if "index=1" in response.url:
            with open(img, "wb") as f:
                f.write(buffer)
    route.continue_()

with sync_playwright() as p:
    #browser = p.chromium.launch(channel="msedge",proxy={"server": "http://{}".format(proxy)})
    browser = p.chromium.launch(channel="msedge")
    iphone_12 = p.devices["iPhone 12"]
    context = browser.new_context(
        **iphone_12,
    )
    page = context.new_page()
    # 下载指定规则的验证码图片
    page.route("**/t.captcha.qq.com/hycdn**", handle_captcha)
    page.goto(
        "https://wap.showstart.com/pages/passport/login/login?redirect=%252Fpages%252FmyHome%252FmyHome")
    page.fill("uni-view.form-phone > uni-input > div > input", "12345104596")
    page.locator("uni-view:nth-child(2) > uni-view.btn").click()

    print("downloading captcha...")

    retryTimes = 10
    for i in range(retryTimes):
        print(f"识别验证码距离中，当前等待轮数{i}/{retryTimes}")
        try:
            res = qq_mark_pos(img)
            distance = res.x.values[0]
            if distance > 0:
                print(f"获取到缺口距离：{distance}")
                break
        except Exception as e:
            print(f"识别错误, 异常：{e}")

        page.wait_for_timeout(500)

    if distance <= 0:
        print("识别失败，退出程序")
    else:
        # 通过页面上验证码框的宽高，计算相对位置
        true_distance = distance * 353 / 680
        move_distance = get_track_list(true_distance)
        print(f"获取到相对滑动距离{true_distance}, 模拟拖动列表{move_distance}")
        print("开始拖动滑块...")
        
        for i in range(retryTimes):
            slider_box = page.frame_locator("#tcaptcha_iframe").locator(
                "#tcaptcha_drag_thumb").bounding_box( )
            if slider_box is not None and slider_box["x"]> 0:
                break;
  
        print(f"{slider_box}")
        
        page.mouse.move(slider_box["x"] + slider_box["width"] / 2,
                        slider_box["y"] + slider_box["height"] / 2)
        page.mouse.down()

        location_x = slider_box["x"]
        for i in move_distance:
            location_x += i
            page.mouse.move(location_x, slider_box["y"])
            page.wait_for_timeout(50)
        page.mouse.up()

        page.wait_for_timeout(1000 * 10)

    browser.close()
