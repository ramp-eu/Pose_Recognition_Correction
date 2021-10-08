# better_factory

1. Install the required python packages using `pip install -r requirements.txt`.
2. Use `git lfs fetch && git lfs pull` to get the models.
3. Use `python wpc.py -m models/FP32/human-pose-estimation-3d-0001.xml` to run the app.

```
The models are obtained from : https://github.com/openvinotoolkit/open_model_zoo
and the `pose_extractor.so` file is built from the openvino pose extractor build `https://github.com/openvinotoolkit/open_model_zoo/tree/master/demos/human_pose_estimation_3d_demo/python`
```
