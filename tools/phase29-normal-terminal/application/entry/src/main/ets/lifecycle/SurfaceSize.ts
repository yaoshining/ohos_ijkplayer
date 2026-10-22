export interface SurfaceRectangle {
  surfaceWidth: number;
  surfaceHeight: number;
}

export interface PixelSize {
  width: number;
  height: number;
}

export function surfacePixels(rect: SurfaceRectangle): PixelSize {
  const width = Math.round(rect.surfaceWidth);
  const height = Math.round(rect.surfaceHeight);
  if (!Number.isFinite(width) || !Number.isFinite(height) ||
      width <= 0 || height <= 0 || width > 2147483647 || height > 2147483647) {
    throw new Error('Surface 像素尺寸无效');
  }
  return { width, height };
}
