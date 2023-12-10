from google.cloud import videointelligence
from flask import current_app
import os
import io
import cv2
import csv
import math


def make_video(file_path, out_file_name):
    result = get_video_api(file_path)
    if isinstance(result, str):
        return False
    cap = cv2.VideoCapture(file_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter.fourcc(*"mp4v")
    # fourcc = cv2.VideoWriter.fourcc(*"H264")

    # get video info
    result_path = os.path.join(
        current_app.config["RESULT_FOLDER"], out_file_name + ".mp4"
    )
    out = cv2.VideoWriter(result_path, fourcc, fps, (width, height))
    # out = skvideo.io.FFmpegWriter(result_path, outputdict={"-vcodec": "libx264"})

    # write video
    # set google api response
    time_to_boxes = {}
    for object_annotation in result.annotation_results[0].object_annotations:
        description = object_annotation.entity.description
        for annotation_frame in object_annotation.frames:
            frame_time_seconds = annotation_frame.time_offset.total_seconds()
            bounding_box = annotation_frame.normalized_bounding_box

            if frame_time_seconds not in time_to_boxes:
                time_to_boxes[frame_time_seconds] = []

            time_to_boxes[frame_time_seconds].append((bounding_box, description))

    # output labels txt file
    label_path = os.path.join(
        current_app.config["LABEL_FOLDER"], out_file_name + ".csv"
    )
    make_label_file(result, label_path)

    while cap.isOpened():
        ret, frame_image = cap.read()
        if not ret:
            break

        current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        # 找到與當前時間最接近的 label
        closest_time = min(time_to_boxes.keys(), key=lambda t: abs(t - current_time))

        # 繪製所有邊框
        for box, desc in time_to_boxes[closest_time]:
            left, right = int(box.left * width), int(box.right * width)
            top, bottom = int(box.top * height), int(box.bottom * height)
            cv2.rectangle(
                frame_image,
                (left, top),
                (right, bottom),
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame_image,
                desc,
                (left, top + 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 255, 0),
                2,
            )

        # write img by fps
        out.write(frame_image)

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    return result_path, label_path


def get_video_api(filepath):
    with io.open(filepath, "rb") as file:
        video = file.read()

    operation = client.annotate_video(
        request={"features": features, "input_content": video}
    )

    try:
        # get result from google video intelligence and set time out 900 seconds
        result = operation.result(timeout=900)
    except Exception as e:
        return str(e)
    return result


def make_label_file(result, label_path):
    with open(label_path, "w", newline="") as file:
        writer = csv.writer(file)
        # 寫入標題行
        writer.writerow(
            [
                "Entity Description",
                "Entity ID",
                "Segment Start",
                "Segment End",
                "Confidence",
                "Time Offset",
                "Left",
                "Top",
                "Right",
                "Bottom",
            ]
        )

        for object_annotation in result.annotation_results[0].object_annotations:
            entity_description = object_annotation.entity.description
            entity_id = (
                object_annotation.entity.entity_id
                if object_annotation.entity.entity_id
                else "N/A"
            )

            segment_start = (
                object_annotation.segment.start_time_offset.seconds
                + object_annotation.segment.start_time_offset.microseconds / 1e6
            )
            segment_end = (
                object_annotation.segment.end_time_offset.seconds
                + object_annotation.segment.end_time_offset.microseconds / 1e6
            )

            confidence = object_annotation.confidence

            # 只針對段落的第一幀
            frame = object_annotation.frames[0]
            time_offset = (
                frame.time_offset.seconds + frame.time_offset.microseconds / 1e6
            )
            box = frame.normalized_bounding_box
            left, top, right, bottom = box.left, box.top, box.right, box.bottom

            # 寫入每條記錄
            writer.writerow(
                [
                    entity_description,
                    entity_id,
                    segment_start,
                    segment_end,
                    confidence,
                    time_offset,
                    left,
                    top,
                    right,
                    bottom,
                ]
            )


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return "{} {}".format(s, size_name[i])


if __name__ != "__main__":
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_sever_key.json"
    client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.Feature.OBJECT_TRACKING]
