#!/bin/bash
# Clone Candy Icons
mkdir -p ~/.local/share/icons
if [ ! -d ~/.local/share/icons/candy-icons ]; then
    echo "Cloning Candy Icons..."
    git clone https://github.com/EliverLara/candy-icons.git ~/.local/share/icons/candy-icons
else
    echo "Candy Icons already installed."
fi

# Set GTK theme to use them (creates ~/.config/gtk-3.0/settings.ini if missing)
mkdir -p ~/.config/gtk-3.0
if [ ! -f ~/.config/gtk-3.0/settings.ini ]; then
    echo "[Settings]" > ~/.config/gtk-3.0/settings.ini
    echo "gtk-icon-theme-name=candy-icons" >> ~/.config/gtk-3.0/settings.ini
    echo "gtk-theme-name=Adwaita-dark" >> ~/.config/gtk-3.0/settings.ini # Fallback dark theme
else
    # Simple replace if it exists (very basic)
    sed -i 's/gtk-icon-theme-name=.*/gtk-icon-theme-name=candy-icons/' ~/.config/gtk-3.0/settings.ini
fi

echo "Icons set to Candy-Icons."
