"""Expose Kokoro's per-phoneme durations as an ONNX output named `duration`.

The stock kokoro-v1.0.onnx only returns audio. Its duration predictor output
(/encoder/Gather_output_0, frames per token) is already in the graph; this adds
an Identity node so kokoro-onnx's create_timed() can return real timings.

    python3 scripts/patch_kokoro.py /path/to/kokoro-v1.0.onnx
writes kokoro-v1.0-timed.onnx next to it.
"""

import os
import sys

import onnx
from onnx import TensorProto, helper

src = sys.argv[1]
m = onnx.load(src)
m.graph.node.append(helper.make_node("Identity", ["/encoder/Gather_output_0"], ["duration"], name="expose_duration"))
m.graph.output.append(helper.make_tensor_value_info("duration", TensorProto.INT64, ["num_tokens"]))
dst = os.path.join(os.path.dirname(src), "kokoro-v1.0-timed.onnx")
onnx.save(m, dst)
print("wrote", dst)
