using UnityEngine;

public class MarkerTestManager : MonoBehaviour
{
    public MarkerIcon headMarker;
    public MarkerIcon leftArmMarker;
    public MarkerIcon rightArmMarker;
    public MarkerIcon leftLegMarker;
    public MarkerIcon rightLegMarker;

    // void Update()
    // {
    //     if (Input.GetKeyDown(KeyCode.Alpha3))
    //     {
    //         ShowAllMarkers("error");
    //     }
    //     else if (Input.GetKeyDown(KeyCode.Alpha4))
    //     {
    //         ShowAllMarkers("warning");
    //     }
    //     else if (Input.GetKeyDown(KeyCode.Alpha0))
    //     {
    //         HideAllMarkers();
    //     }
    // }

    // void ShowAllMarkers(string type)
    // {
    //     headMarker.gameObject.SetActive(true);
    //     leftArmMarker.gameObject.SetActive(true);
    //     rightArmMarker.gameObject.SetActive(true);
    //     leftLegMarker.gameObject.SetActive(true);
    //     rightLegMarker.gameObject.SetActive(true);

    //     headMarker.SetIcon(type);
    //     leftArmMarker.SetIcon(type);
    //     rightArmMarker.SetIcon(type);
    //     leftLegMarker.SetIcon(type);
    //     rightLegMarker.SetIcon(type);
    // }

    // void HideAllMarkers()
    // {
    //     headMarker.gameObject.SetActive(false);
    //     leftArmMarker.gameObject.SetActive(false);
    //     rightArmMarker.gameObject.SetActive(false);
    //     leftLegMarker.gameObject.SetActive(false);
    //     rightLegMarker.gameObject.SetActive(false);
    // }
    public PoseReceiverRightLive poseReceiver;
    public PoseSimilarityEvaluator poseSimilarity;


    void Update()
    {
        // UpdateMarkerState(headMarker, poseReceiver.head);
        // UpdateMarkerState(leftArmMarker, poseReceiver.leftArm);
        // UpdateMarkerState(rightArmMarker, poseReceiver.rightArm);
        // UpdateMarkerState(leftLegMarker, poseReceiver.leftLeg);
        // UpdateMarkerState(rightLegMarker, poseReceiver.rightLeg);
        UpdateMarkerState(headMarker, poseSimilarity.head);
        UpdateMarkerState(leftArmMarker, poseSimilarity.leftArm);
        UpdateMarkerState(rightArmMarker, poseSimilarity.rightArm);
        UpdateMarkerState(leftLegMarker, poseSimilarity.leftLeg);
        UpdateMarkerState(rightLegMarker, poseSimilarity.rightLeg);
    }

    void UpdateMarkerState(MarkerIcon marker, float score)
    {
        if (score >= 85f && score <= 100f)
        {
            marker.gameObject.SetActive(false);
        }
        else if (score >= 65f && score < 85f)
        {
            marker.gameObject.SetActive(true);
            marker.SetIcon("warning");
        }
        else if (score < 65f)
        {
            marker.gameObject.SetActive(true);
            marker.SetIcon("error");
        }
    }
}
