/*
 Minimal Node.js script to generate two images using OpenAI Images API
 - Requires OPENAI_API_KEY in .env
 - Outputs saved under outputs/
*/

'use strict';

const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function main() {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    console.error('Error: OPENAI_API_KEY is not set. Create a .env file with OPENAI_API_KEY=your_key');
    process.exit(1);
  }

  let OpenAI;
  try {
    OpenAI = require('openai');
    OpenAI = OpenAI.default || OpenAI;
  } catch (e) {
    console.error('Missing dependency: openai. Run `npm install` first.');
    process.exit(1);
  }

  const client = new OpenAI({ apiKey });

  const outDir = path.resolve(__dirname, '..', 'outputs');
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  const prompt = [
    'Create a realistic illustration (photoreal-leaning illustration) of an adult Asian woman in an everyday outfit.',
    'She wears tight skinny blue jeans and a simple white top.',
    'Setting: natural daylight street scene.',
    'Pose/composition: 3/4 side walking, framed from knees to head, relaxed expression.',
    'Non-sexualized and fully clothed. Avoid nudity, erotic or explicit content, minors, or fetish framing.'
  ].join(' ');

  const outputs = [
    { size: '1024x1024', file: path.join(outDir, 'woman_jeans_1024.png') },
    { size: '1024x1365', file: path.join(outDir, 'woman_jeans_3x4.png') },
  ];

  for (const { size, file } of outputs) {
    try {
      console.log(`Generating image size ${size} ...`);
      const response = await client.images.generate({
        model: 'gpt-image-1',
        prompt,
        size,
      });

      const b64 = response?.data?.[0]?.b64_json;
      if (!b64) {
        throw new Error('API did not return image data.');
      }

      const buffer = Buffer.from(b64, 'base64');
      fs.writeFileSync(file, buffer);
      console.log(`Saved: ${file}`);
    } catch (err) {
      console.error(`Failed to generate ${size}:`, err?.response?.data || err?.message || err);
      process.exitCode = 1;
    }
  }

  if (process.exitCode === 0 || process.exitCode === undefined) {
    console.log('All images generated successfully.');
  } else {
    console.log('Completed with some errors. See logs above.');
  }
}

main();
