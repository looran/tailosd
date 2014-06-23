import time
import aosd_text_scroll

def test_no_scroll(osd):
    osd.append("Hello", "red")
    osd.append("Hello2", "red")
    osd.append("Hello3", "red")
    osd.append("Hello4", "red")
    osd.append("Hello5", "red")
    osd.append("Hello6", "red")
    osd.append("Hello7", "red")
    osd.append("Hello8", "red")
    osd.append("Hello9", "red")
    time.sleep(3)
    osd.append("Hello10", "red")
    time.sleep(1)
    osd.append("Hello11", "red")
    time.sleep(1)
    osd.append("Hello12", "red")
    time.sleep(1)
    osd.append("Hello13", "red")
    time.sleep(1)
    osd.append("Hello14", "red")
    time.sleep(1)
    osd.append("Hello15", "red")
    time.sleep(6)
    osd.append("Hello16", "red")
    time.sleep(1)
    osd.append("Hello17", "red")
    time.sleep(6)

def test_scroll(osd):
    osd.append("Hello", "red")
    time.sleep(1)
    for i in range(2, 60):
        osd.append("Hello%d" % i, "red")
        time.sleep(0.03)
    time.sleep(4)
    for i in range(60, 100):
        osd.append("Hello%d" % i, "red")
        time.sleep(0.03)
    time.sleep(6)

osd = aosd_text_scroll.Aosd_text_scroll_thread()
osd.start()

#test_no_scroll(osd)
test_scroll(osd)

osd.exit()

print
print "END"
