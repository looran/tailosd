class Aosd_object(aosd.Aosd):
    """ Aosd objects should inherit from this class, and surcharge the self._render_object() """
    def __init__(self):
        super(Aosd_object, self).__init__()
        self.set_transparency(aosd.TRANSPARENCY_COMPOSITE)
        self.set_hide_upon_mouse_event(True)
        self.set_renderer(self._render_object, data)

    def _render_object(self, context, data):
        raise Exception("You should surcharge this _render_object() function !")

    def _render_internal_object(self):
        self._render_object()
        context.save()
        context.paint()
        context.restore()

class Aosd_round_rect(Aosd_object):
    def __init__(self):
        super(Aosd_round_rect, self).__init__()

    def _render_object(self):
        context.set_source_rgba(data['alpha'], 0, 0, 0.7)
        self._round_rect(context, 0, 0, 1020, 830, RADIUS)
        context.fill()

        context.set_source_rgba(1, 1, 1, 1.0)
        self._round_rect(context, 10, 10, 1000, 800, RADIUS)
        context.stroke()

    def round_rect(context, x, y, w, h, r):
        context.new_path()
        context.move_to(x+r, y)
        context.line_to(x+w-r, y) # top edge
        context.curve_to(x+w, y, x+w, y, x+w, y+r)
        context.line_to(x+w, y+h-r) # right edge
        context.curve_to(x+w, y+h, x+w, y+h, x+w-r, y+h)
        context.line_to(x+r, y+h) # bottom edge
        context.curve_to(x, y+h, x, y+h, x, y+h-r)
        context.line_to(x, y+r) # left edge
        context.curve_to(x, y, x, y, x+r, y)
        context.close_path()
