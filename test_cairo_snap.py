import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2, GLib
import cairo

def test():
    win = Gtk.Window()
    win.set_default_size(800, 600)
    wv = WebKit2.WebView()
    win.add(wv)
    wv.load_html("<html><body style='background: red; width: 100vw; height: 100vh;'><h1>Hello Cairo</h1></body></html>")
    win.show_all()

    def capture():
        alloc = wv.get_allocation()
        w, h = alloc.width, alloc.height
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surface)
        wv.draw(cr)
        surface.write_to_png("test_cairo.png")
        print("saved cairo")
        Gtk.main_quit()

    GLib.timeout_add(1500, capture)

test()
Gtk.main()
