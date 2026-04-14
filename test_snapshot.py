import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2, GLib, Gdk

def test():
    win = Gtk.Window()
    win.set_default_size(800, 600)
    wv = WebKit2.WebView()
    win.add(wv)
    wv.load_html("<html><body style='background: blue; width: 100vw; height: 100vh;'>Hello</body></html>")
    win.show_all()

    def capture():
        def on_snap(wv, res):
            surf = wv.get_snapshot_finish(res)
            w, h = surf.get_width(), surf.get_height()
            pb = Gdk.pixbuf_get_from_surface(surf, 0, 0, w, h)
            pb.savev("test_visible.png", "png", [], [])
            print("saved visible")
            
            # Now try full dev
            def on_snap_full(wv, res):
                surf = wv.get_snapshot_finish(res)
                w, h = surf.get_width(), surf.get_height()
                pb = Gdk.pixbuf_get_from_surface(surf, 0, 0, w, h)
                pb.savev("test_full.png", "png", [], [])
                print("saved full")
                Gtk.main_quit()

            wv.get_snapshot(WebKit2.SnapshotRegion.FULL_DOCUMENT, WebKit2.SnapshotOptions.NONE, None, on_snap_full)
        
        wv.get_snapshot(WebKit2.SnapshotRegion.VISIBLE, WebKit2.SnapshotOptions.NONE, None, on_snap)
        return False

    GLib.timeout_add(1000, capture)

test()
Gtk.main()
