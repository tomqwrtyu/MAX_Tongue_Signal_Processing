using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ouob : MonoBehaviour
{
    //[SerializeField] double speed = 10f;
    public float speed = 10f;
    // Start is called before the first frame update
    void Start()
    {
        UnityEngine.Debug.Log($"ouob");
    }

    // Update is called once per frame
    void Update()
    {
        transform.Translate(speed * Time.deltaTime, speed * Time.deltaTime, 0);
        //_SerialPort.ReadLine();
        //_SerialPort.WriteLine();
    }
}
