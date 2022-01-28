import _tkinter
import tkinter as tk
import unittest
import main


class TKTestCase(unittest.TestCase):
    """
    https://stackoverflow.com/questions/4083796/how-do-i-run-unittest-on-a-tkinter-app
    These methods are going to be the same for every GUI test,
    so refactored them into a separate class
    """

    def setUp(self):
        self.root = tk.Tk()
        self.pump_events()
        self.client_app: main.ClientApp = main.ClientApp(self.root)

    def tearDown(self):
        if self.root:
            self.root.destroy()
            self.pump_events()

    def pump_events(self):
        while self.root.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
            pass


class TestClientApp(TKTestCase):
    def test_load_options_frame(self):
        self.assertIsInstance(self.client_app.options_frame, main.OptionsFrame)

    def test_load_result_display_frame(self):
        self.assertIsInstance(self.client_app.result_display_frame, main.ResultDisplayFrame)


class TestOptionsFrame(TKTestCase):
    def test_children_packed(self):
        all_widgets = [widget._name for widget in self.client_app.options_frame.winfo_children()]
        packed_widgets = [widget._name for widget in self.client_app.options_frame.pack_slaves()]
        # not all widgets are loaded on init.
        self.assertNotEqual(len(all_widgets), len(packed_widgets))

        # widget criteria met to load all widgets
        self.client_app.options_frame.log_list_var.set('PAS')
        self.client_app.options_frame.radio_selected()
        all_widgets = [widget._name for widget in self.client_app.options_frame.winfo_children()]
        packed_widgets = [widget._name for widget in self.client_app.options_frame.pack_slaves()]
        all_widgets.sort()
        packed_widgets.sort()
        self.assertListEqual(all_widgets, packed_widgets)

    def test_title_label(self):
        self.assertIsInstance(self.client_app.options_frame.title, tk.Label)
        self.assertEqual(self.client_app.options_frame.title['text'], 'Logger')
        self.assertEqual(self.client_app.options_frame.title['background'], main.BACKGROUND)
        self.assertEqual(self.client_app.options_frame.title['foreground'], main.FOREGROUND)

    def test_radio_button_name_and_value(self):
        for suffix in main.Suffix:
            rb_widget = self.client_app.options_frame.nametowidget(f'rb_{suffix.name}')
            self.assertIsInstance(rb_widget, main.RadioButton)
            self.assertEqual(rb_widget['text'], suffix.name)
            self.assertEqual(rb_widget['value'], suffix.name)

    def test_button_hover(self):
        for button in [widget._name for widget in self.client_app.options_frame.winfo_children() if widget._name.startswith('btn')]:
            rb_widget = self.client_app.options_frame.nametowidget(f'{button}')

            rb_widget.on_enter()
            self.assertEqual(rb_widget['background'], main.BACKGROUND_2)
            self.assertEqual(rb_widget['foreground'], main.WHITE_TEXT)

            rb_widget.on_leave()
            self.assertEqual(rb_widget['background'], main.BACKGROUND)
            self.assertEqual(rb_widget['foreground'], main.FOREGROUND)

    def test_radio_button_var(self):
        for suffix in main.Suffix:
            rb_widget = self.client_app.options_frame.nametowidget(f'rb_{suffix.name}')
            rb_widget.invoke()
            self.assertEqual(suffix.name, self.client_app.options_frame.log_list_var.get())


if __name__ == '__main__':
    unittest.main()
