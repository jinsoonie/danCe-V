using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Video;

public class CompareSceneVideoLoader : MonoBehaviour
{
    public PoseReceiverLeftRef poseReceiver;  // drag the PoseReceiver GameObject here in Inspector to retrieve public hasStartedVideo flag

    public VideoPlayer videoPlayer;
    public RawImage videoDisplay;  // Assign to VideoDisplay RawImage in Inspector

    private bool videoReady = false;

    void Start()
    {
        string videoPath = MainMenuScript.videoPath;

        if (!string.IsNullOrEmpty(videoPath))
        {
            videoPlayer.source = VideoSource.Url;
            videoPlayer.url = "file://" + videoPath;
            videoPlayer.aspectRatio = VideoAspectRatio.FitInside; // prevent cropping
            videoPlayer.Prepare();
            videoPlayer.prepareCompleted += OnVideoPrepared;
            Debug.Log("Preparing video at: " + videoPath);
        }
        else
        {
            Debug.LogWarning("No video path found for vid player.");
        }
    }

    void OnVideoPrepared(VideoPlayer vp)
    {
        videoReady = true;

        // resize RawImage to match video dimensions
        if (videoDisplay != null)
        {
            RectTransform rt = videoDisplay.GetComponent<RectTransform>();
            rt.sizeDelta = new Vector2(2400, 1440); // fixed area
        }

        Debug.Log("Video prepared. Press Spacebar to start.");
    }

    void Update()
    {
        // Automatically play the video ONCE when poseReceiver.hasStartedVideo becomes true
        if (videoReady && poseReceiver != null && poseReceiver.hasStartedVideo)
        {
            // Play video if not already playing, and disable auto-play after first trigger
            if (!videoPlayer.isPlaying)
            {
                Debug.Log("Auto-playing video ONCE from poseReceiver.");
                videoPlayer.Play();

                // Reset the flag so it doesn't keep triggering
                poseReceiver.hasStartedVideo = false;
            }
        }

        if (videoReady && Input.GetKeyDown(KeyCode.Space) && poseReceiver.hasStartedVideo)
        {
            if (videoPlayer.isPlaying)
            {
                Debug.Log("PAUSING VIDEO");
                videoPlayer.Pause();
            }
            else
            {
                Debug.Log("PLAYING VIDEO");
                videoPlayer.Play();
            }
        }
    }
}
