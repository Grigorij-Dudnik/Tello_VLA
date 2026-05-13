import pickle
import socket

import numpy as np
from lerobot.configs.policies import PreTrainedConfig
from lerobot.policies.factory import get_policy_class, make_pre_post_processors
from lerobot.utils.control_utils import predict_action
from lerobot.utils.device_utils import get_safe_torch_device


POLICY = "Grigorij/xvla_Red_apple_sum"
TASK = "Fly to the red apple"
DEVICE = "cuda"
PORT = 5005

cfg = PreTrainedConfig.from_pretrained(POLICY)
cfg.device = DEVICE
policy = get_policy_class(cfg.type).from_pretrained(POLICY, config=cfg).to(DEVICE).eval()
pre, post = make_pre_post_processors(policy_cfg=cfg, pretrained_path=POLICY, preprocessor_overrides={"device_processor": {"device": DEVICE}})
device = get_safe_torch_device(DEVICE)

s = socket.socket()
s.bind(("0.0.0.0", PORT))
s.listen(1)
conn, _ = s.accept()
f = conn.makefile("rwb")

while True:
    obs = pickle.load(f)
    action = predict_action(
        observation={
            "observation.images.camera_front": obs["rgb"],
            "observation.state": np.array([obs["height"]], dtype=np.float32),
        },
        policy=policy,
        device=device,
        task=TASK,
        preprocessor=pre,
        postprocessor=post,
        use_amp=cfg.use_amp,
    ).squeeze().float().numpy()
    pickle.dump(np.clip(action, -1, 1), f)
    f.flush()
