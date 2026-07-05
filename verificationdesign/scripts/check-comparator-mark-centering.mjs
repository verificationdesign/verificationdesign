import assert from 'node:assert/strict';
import { inflateSync } from 'node:zlib';
import puppeteer from 'puppeteer';

const url = process.env.SITE_URL || 'http://127.0.0.1:4321/';
const deviceScaleFactor = Number(process.env.DEVICE_SCALE_FACTOR || 2);
const maxCssOffset = Number(process.env.MAX_CSS_OFFSET || 1);

function readUInt32(buffer, offset) {
  return buffer.readUInt32BE(offset);
}

function paeth(left, up, upperLeft) {
  const p = left + up - upperLeft;
  const pa = Math.abs(p - left);
  const pb = Math.abs(p - up);
  const pc = Math.abs(p - upperLeft);
  if (pa <= pb && pa <= pc) return left;
  if (pb <= pc) return up;
  return upperLeft;
}

function decodePngRgba(buffer) {
  assert.equal(buffer.toString('hex', 0, 8), '89504e470d0a1a0a', 'screenshot is not a PNG');

  let width = 0;
  let height = 0;
  let channels = 0;
  const idat = [];

  for (let offset = 8; offset < buffer.length;) {
    const length = readUInt32(buffer, offset);
    const type = buffer.toString('ascii', offset + 4, offset + 8);
    const dataStart = offset + 8;
    const dataEnd = dataStart + length;
    const data = buffer.subarray(dataStart, dataEnd);

    if (type === 'IHDR') {
      width = readUInt32(data, 0);
      height = readUInt32(data, 4);
      const bitDepth = data[8];
      const colorType = data[9];
      assert.equal(bitDepth, 8, 'expected an 8-bit PNG screenshot');
      assert.ok(colorType === 2 || colorType === 6, 'expected an RGB or RGBA PNG screenshot');
      channels = colorType === 6 ? 4 : 3;
    } else if (type === 'IDAT') {
      idat.push(data);
    } else if (type === 'IEND') {
      break;
    }

    offset = dataEnd + 4;
  }

  const stride = width * channels;
  const inflated = inflateSync(Buffer.concat(idat));
  const pixels = Buffer.alloc(width * height * channels);
  let source = 0;

  for (let y = 0; y < height; y += 1) {
    const filter = inflated[source];
    source += 1;
    const row = inflated.subarray(source, source + stride);
    source += stride;

    for (let x = 0; x < stride; x += 1) {
      const left = x >= channels ? pixels[y * stride + x - channels] : 0;
      const up = y > 0 ? pixels[(y - 1) * stride + x] : 0;
      const upperLeft = y > 0 && x >= channels ? pixels[(y - 1) * stride + x - channels] : 0;
      let predictor = 0;

      if (filter === 1) predictor = left;
      else if (filter === 2) predictor = up;
      else if (filter === 3) predictor = Math.floor((left + up) / 2);
      else if (filter === 4) predictor = paeth(left, up, upperLeft);
      else assert.equal(filter, 0, `unsupported PNG filter ${filter}`);

      pixels[y * stride + x] = (row[x] + predictor) & 0xff;
    }
  }

  return { width, height, pixels };
}

function measureForeground({ width, height, pixels }) {
  const background = [pixels[0], pixels[1], pixels[2]];
  const channels = pixels.length / (width * height);
  let count = 0;
  let sumX = 0;
  let sumY = 0;
  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const offset = (y * width + x) * channels;
      const delta =
        Math.abs(pixels[offset] - background[0]) +
        Math.abs(pixels[offset + 1] - background[1]) +
        Math.abs(pixels[offset + 2] - background[2]);

      const alpha = channels === 4 ? pixels[offset + 3] : 255;
      if (alpha > 8 && delta > 20) {
        count += 1;
        sumX += x + 0.5;
        sumY += y + 0.5;
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
      }
    }
  }

  assert.ok(count > 0, 'no foreground pixels found in comparator mark screenshot');

  return {
    count,
    minX,
    maxX,
    minY,
    maxY,
    centroidX: sumX / count,
    centroidY: sumY / count,
    centerX: width / 2,
    centerY: height / 2,
  };
}

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--no-sandbox'],
});

try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800, deviceScaleFactor });
  await page.goto(url, { waitUntil: 'networkidle0' });
  await page.evaluate(() => new Promise((resolve) => setTimeout(resolve, 1800)));

  const clip = await page.evaluate(() => {
    const mark = document.querySelector('.site-header .comparator-mark');
    if (!(mark instanceof HTMLElement)) {
      throw new Error('missing header comparator mark');
    }
    const rect = mark.getBoundingClientRect();
    return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
  });

  const screenshot = Buffer.from(await page.screenshot({ clip }));
  const image = decodePngRgba(screenshot);
  const measurement = measureForeground(image);
  const offsetX = (measurement.centroidX - measurement.centerX) / deviceScaleFactor;
  const offsetY = (measurement.centroidY - measurement.centerY) / deviceScaleFactor;

  console.log(JSON.stringify({ url, clip, image: { width: image.width, height: image.height }, measurement, offsetCssPx: { x: offsetX, y: offsetY } }, null, 2));

  assert.ok(
    Math.abs(offsetX) <= maxCssOffset && Math.abs(offsetY) <= maxCssOffset,
    `comparator mark foreground is not centered: offset ${offsetX.toFixed(2)}px, ${offsetY.toFixed(2)}px`,
  );
} finally {
  await browser.close();
}
