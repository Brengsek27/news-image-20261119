import { copyFile, mkdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { readFile } from 'node:fs/promises';

const source = new URL('./entry.png', import.meta.url);
const sourceBytes = await readFile(source);
const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
if (sourceBytes.length > 1_048_576) {
  throw new Error(`PNG exceeds the 1 MiB limit: ${sourceBytes.length} bytes`);
}
if (sourceBytes.length < 24 || !sourceBytes.subarray(0, 8).equals(signature)) {
  throw new Error('Source is not a valid PNG file');
}
if (sourceBytes.readUInt32BE(8) !== 13 || sourceBytes.toString('ascii', 12, 16) !== 'IHDR') {
  throw new Error('PNG is missing a valid IHDR chunk');
}
const width = sourceBytes.readUInt32BE(16);
const height = sourceBytes.readUInt32BE(20);
if (width !== 1024 || height !== 1024) {
  throw new Error(`PNG dimensions must be 1024x1024, got ${width}x${height}`);
}
const outputDirectory = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
await mkdir(outputDirectory, { recursive: true });
const destination = join(outputDirectory, 'entry.png');
await copyFile(source, destination);
const copied = await stat(destination);
console.log(`Copied ${copied.size} bytes`);
