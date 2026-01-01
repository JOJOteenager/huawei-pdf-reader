"""
PDF Reader - Main Entry Point
Minimal Kivy app for Android testing
"""

# Kivy configuration must be set before importing kivy modules
import os
os.environ['KIVY_LOG_LEVEL'] = 'debug'

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class PDFReaderApp(App):
    """PDF Reader Application"""
    
    def build(self):
        """Build the UI"""
        # Simple layout
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Title - using ASCII only to avoid font issues
        title = Label(
            text='PDF Reader',
            font_size='32sp',
            size_hint_y=0.3
        )
        layout.add_widget(title)
        
        # Version
        version = Label(
            text='Version 0.1.0',
            font_size='18sp',
            size_hint_y=0.2
        )
        layout.add_widget(version)
        
        # Status
        self.status = Label(
            text='App Ready',
            font_size='16sp',
            size_hint_y=0.2
        )
        layout.add_widget(self.status)
        
        # Button
        btn = Button(
            text='Start',
            font_size='20sp',
            size_hint_y=0.3
        )
        btn.bind(on_press=self.on_start)
        layout.add_widget(btn)
        
        return layout
    
    def on_start(self, instance):
        """Button click handler"""
        self.status.text = 'Button clicked!'


def main():
    """Main entry point"""
    PDFReaderApp().run()


if __name__ == '__main__':
    main()
