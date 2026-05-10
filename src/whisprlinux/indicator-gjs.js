#!/usr/bin/gjs

imports.gi.versions.Gtk = '3.0';
imports.gi.versions.Gdk = '3.0';
imports.gi.versions.GdkPixbuf = '2.0';
cairo = imports.cairo;

const GLib = imports.gi.GLib;
const Gdk = imports.gi.Gdk;
const GdkPixbuf = imports.gi.GdkPixbuf;
const Gtk = imports.gi.Gtk;

Gtk.init(null);

const assetPath = ARGV[0];
const pixbuf = GdkPixbuf.Pixbuf.new_from_file(assetPath);
const screen = Gdk.Screen.get_default();
const visual = screen.get_rgba_visual();

const window = new Gtk.Window({
    type: Gtk.WindowType.POPUP,
    decorated: false,
    skip_taskbar_hint: true,
    skip_pager_hint: true,
    resizable: false,
    app_paintable: true,
});

if (visual) {
    window.set_visual(visual);
}

window.set_keep_above(true);
window.set_accept_focus(false);
window.set_focus_on_map(false);
window.set_default_size(pixbuf.get_width(), pixbuf.get_height());

const image = Gtk.Image.new_from_pixbuf(pixbuf);
window.add(image);

window.connect('draw', (_widget, cr) => {
    cr.setSourceRGBA(0, 0, 0, 0);
    cr.setOperator(cairo.Operator.SOURCE);
    cr.paint();
    cr.setOperator(cairo.Operator.OVER);
    return false;
});

window.connect('destroy', () => Gtk.main_quit());
window.show_all();

const display = Gdk.Display.get_default();
const monitor = display.get_primary_monitor() || display.get_monitor(0);
const geometry = monitor.get_geometry();
const x = geometry.x + Math.floor((geometry.width - pixbuf.get_width()) / 2);
const y = geometry.y + geometry.height - pixbuf.get_height() - 90;
window.move(Math.max(x, geometry.x), Math.max(y, geometry.y));

GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, 2, () => {
    window.destroy();
    return GLib.SOURCE_REMOVE;
});
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, 15, () => {
    window.destroy();
    return GLib.SOURCE_REMOVE;
});

Gtk.main();
