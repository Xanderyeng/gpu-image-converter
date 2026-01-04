import pytest
from pathlib import Path
from app.converter import GPUImageConverter


@pytest.fixture
def converter():
    return GPUImageConverter()


@pytest.fixture
def sample_image(tmp_path):
    """Create a simple test image."""
    from PIL import Image

    img = Image.new('RGB', (800, 600), color='red')
    img_path = tmp_path / "test.png"
    img.save(img_path)
    return str(img_path)


def test_converter_initialization(converter):
    """Test converter initializes properly."""
    assert converter is not None
    assert isinstance(converter.cuda_available, bool)


def test_png_to_webp_conversion(converter, sample_image, tmp_path):
    """Test basic PNG to WebP conversion."""
    output_path = tmp_path / "output.webp"

    result = converter.convert(
        input_path=sample_image,
        output_path=str(output_path),
        output_format='webp',
        quality=90
    )

    assert result['success'] is True
    assert Path(output_path).exists()
    assert result['format'] == 'webp'
    assert result['output_size'] > 0


def test_resize_image(converter, sample_image, tmp_path):
    """Test image resizing."""
    output_path = tmp_path / "resized.jpg"

    result = converter.convert(
        input_path=sample_image,
        output_path=str(output_path),
        output_format='jpg',
        width=400,
        height=300,
        fit='max'
    )

    assert result['success'] is True
    assert result['output_dimensions'] == (400, 300)


def test_batch_conversion(converter, tmp_path):
    """Test batch conversion."""
    from PIL import Image

    # Create multiple test images
    files = []
    for i in range(3):
        img = Image.new('RGB', (100, 100), color='blue')
        img_path = tmp_path / f"test_{i}.png"
        img.save(img_path)
        files.append(str(img_path))

    output_dir = tmp_path / "output"

    results = converter.batch_convert(
        files=files,
        output_dir=str(output_dir),
        output_format='webp',
        quality=80
    )

    assert len(results) == 3
    assert all(r['success'] for r in results)