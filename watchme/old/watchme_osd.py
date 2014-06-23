class Watchme_osd_OLD(multiprocessing.Process):
    """ Where the OSD display happpends
    Runs as X session user """
    def __init__(self, logger, queue):
        super(Watchme_osd, self).__init__()
        init_from_args(self)

    def run(self):
        title = setproctitle.getproctitle()
        setproctitle.setproctitle(title + " osd")
        #droppriv('laurent', 'laurent') # XXX get X session user
        droppriv('nobody', 'nogroup') # XXX get X session user
        self.logger.info("after droppriv")
        osd = self._setup()

        while True:
            self.logger.debug("XXX loop")
            evt = self.queue.get()
            txt = "%s %s" % (evt.source, evt.content)
            width, height = self._set_string(osd, txt)
            self._scroll(osd, width, height)

    def _scroll(self, osd, width, height):
        pos = 8
        step = 3
        
        osd.set_position(pos, width, height)
        (x, y, _, _) = osd.get_geometry()
        osd.set_position_offset(width, height)
        osd.show()

        x -= 1
        y += height - 1;
        for i in range(1, height + 1, step):
            osd.loop_for(20)
            y -= step
            osd.set_geometry(x, y, width, i)

        osd.set_position(pos, width, height)
        osd.set_position_offset(-1, -1)
        (x, y, _, _) = osd.get_geometry()
        osd.loop_for(2000)

        for i in range(height, 0, -step):
            y += step
            osd.set_geometry(x, y, width, i);
            osd.loop_for(20);

        osd.hide();

    def _setup(self):
        osd = aosd.AosdText()
        osd.set_transparency(aosd.TRANSPARENCY_COMPOSITE)
        if osd.get_transparency() != aosd.TRANSPARENCY_COMPOSITE:
            osd.set_transparency(aosd.TRANSPARENCY_NONE)
        
        osd.geom_x_offset = 10
        osd.geom_y_offset = 10
        
        osd.back_color = "white"
        osd.back_opacity = 80

        osd.shadow_color = "black"
        osd.shadow_opacity = 127
        osd.shadow_x_offset = 2
        osd.shadow_y_offset = 2

        osd.fore_color = "green"
        osd.fore_opacity = 255
        
        osd.set_font("Times New Roman Italic 24")
        osd.wrap = aosd.PANGO_WRAP_WORD_CHAR
        osd.alignment = aosd.PANGO_ALIGN_RIGHT
        osd.set_layout_width(osd.get_screen_wrap_width())
        return osd

    def _set_string(self, osd, text):
        osd.set_text(text)
        return osd.get_text_size()

