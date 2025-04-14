using UnityEngine;

public class MarkerTestManager : MonoBehaviour
{
    public MarkerIcon headMarker;
    public MarkerIcon leftArmMarker;
    public MarkerIcon rightArmMarker;
    public MarkerIcon leftLegMarker;
    public MarkerIcon rightLegMarker;

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Alpha3))
        {
            ShowAllMarkers("error");
        }
        else if (Input.GetKeyDown(KeyCode.Alpha4))
        {
            ShowAllMarkers("warning");
        }
        else if (Input.GetKeyDown(KeyCode.Alpha0))
        {
            HideAllMarkers();
        }
    }

    void ShowAllMarkers(string type)
    {
        headMarker.gameObject.SetActive(true);
        leftArmMarker.gameObject.SetActive(true);
        rightArmMarker.gameObject.SetActive(true);
        leftLegMarker.gameObject.SetActive(true);
        rightLegMarker.gameObject.SetActive(true);

        headMarker.SetIcon(type);
        leftArmMarker.SetIcon(type);
        rightArmMarker.SetIcon(type);
        leftLegMarker.SetIcon(type);
        rightLegMarker.SetIcon(type);
    }

    void HideAllMarkers()
    {
        headMarker.gameObject.SetActive(false);
        leftArmMarker.gameObject.SetActive(false);
        rightArmMarker.gameObject.SetActive(false);
        leftLegMarker.gameObject.SetActive(false);
        rightLegMarker.gameObject.SetActive(false);
    }
}
