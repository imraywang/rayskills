# Code adapted from Peter Yang's video-short

`review_page.py` and `review.py` (review page), `qa_video.py` (render checks), `cut_retakes.py` (retake / dead-air
cutting rules) and `capture_page.py` (page capture) adapt code and ideas from https://github.com/petergyang/video-short
(commit 524edcf, 2026-10-20). Changes: Chinese UI, Tailscale listener, scenes from scenes.json / timeline.json,
energy-based pause detection and pause-snapped cuts for Chinese Whisper timings, landscape capture width.

MIT License

Copyright (c) 2026 Peter Yang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
