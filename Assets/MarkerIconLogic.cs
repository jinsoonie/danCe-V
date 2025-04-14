using UnityEngine;

public class MarkerIcon : MonoBehaviour
{
    public Material redErrorMaterial;
    public Material yellowWarningMaterial;

    private Renderer rend;

    void Awake()
    {
        rend = GetComponent<Renderer>();
    }

    public void SetIcon(string type)
    {
        if (type == "error")
        {
            rend.material = redErrorMaterial;
        }
        else if (type == "warning")
        {
            rend.material = yellowWarningMaterial;
        }
        else
        {
            Debug.LogWarning("Unknown icon type: " + type);
        }
    }
}
