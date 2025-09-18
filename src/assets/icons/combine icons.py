from PIL import Image


def combine_icons():
    # Load the images
    camera_path = (
        r"PhotoOrganizer_v3\icons\camera\android-chrome-512x512.png"  # Camera icon
    )
    folder_path = (
        r"PhotoOrganizer_v3\icons\separator\android-chrome-512x512.png"  # Folder icon
    )

    try:
        camera = Image.open(camera_path)
        folder = Image.open(folder_path)

        # Get the folder size and make camera smaller (about 50% of folder size)
        base_size = folder.size[0]  # Assuming square icons
        camera_size = int(base_size * 0.5)
        camera = camera.resize((camera_size, camera_size), Image.Resampling.LANCZOS)

        # Create a new image with the folder as base
        combined = folder.copy()

        # Calculate position for bottom right (with less padding to move more right)
        x_pos = base_size - camera_size - 50
        y_pos = base_size - camera_size - 15

        # Paste camera on top of folder (use camera as mask if it has transparency)
        if camera.mode == "RGBA":
            combined.paste(camera, (x_pos, y_pos), camera)
        else:
            combined.paste(camera, (x_pos, y_pos))


        # Save as ICO file with multiple sizes
        output_path = r"PhotoOrganizer_v3\icons\Photo Organizer icon.ico"
        combined.save(
            output_path,
            format="ICO",
            sizes=[
                (16, 16),
                (24, 24),
                (32, 32),
                (48, 48),
                (64, 64),
                (128, 128),
                (256, 256),
            ],
        )
        print(f"Combined icon saved as: {output_path}")

        # Also save as PNG for preview
        png_path = r"PhotoOrganizer_v3\icons\Photo Organizer icon.png"
        combined.save(png_path)
        print(f"PNG version saved as: {png_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(
            "Please ensure you have the camera and separator folders with their icon files."
        )
        

if __name__ == "__main__":
    combine_icons()
