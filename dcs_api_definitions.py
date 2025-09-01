"""DCS API 定义模块 - 包含所有已知的 DCS API 定义"""

DCS_APIS = [
    {
        "id": 2,
        "returns_data": False,
        "api_syntax": "GetDevice(device_id):set_argument_value(argument_id, new_value)",
        "parameter_count": 3,
        "parameter_defs": [
            {"id": 0, "name": "device_id", "type": 0},
            {"id": 1, "name": "argument_id", "type": 0},
            {"id": 2, "name": "new_value", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 6,
        "returns_data": True,
        "api_syntax": "GetDevice(device_id):get_frequency()",
        "parameter_count": 1,
        "parameter_defs": [
            {"id": 0, "name": "device_id", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 7,
        "returns_data": False,
        "api_syntax": "GetDevice(device_id):set_frequency(new_value)",
        "parameter_count": 2,
        "parameter_defs": [
            {"id": 0, "name": "device_id", "type": 0},
            {"id": 1, "name": "new_value", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 8,
        "returns_data": True,
        "api_syntax": "GetDevice(device_id):update_arguments()",
        "parameter_count": 1,
        "parameter_defs": [
            {"id": 0, "name": "device_id", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 9,
        "returns_data": True,
        "api_syntax": "LoGetAircraftDrawArgumentValue(draw_argument_id)",
        "parameter_count": 1,
        "parameter_defs": [
            {"id": 0, "name": "draw_argument_id", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 10,
        "returns_data": True,
        "api_syntax": "LoGetObjectById(object_id)",
        "parameter_count": 1,
        "parameter_defs": [
            {"id": 0, "name": "object_id", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 11,
        "returns_data": True,
        "api_syntax": "list_indication(indicator_id)",
        "parameter_count": 1,
        "parameter_defs": [
            {"id": 0, "name": "indicator_id", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 12,
        "returns_data": False,
        "api_syntax": "LoSetCommand(iCommand)",
        "parameter_count": 1,
        "parameter_defs": [
            {"id": 0, "name": "iCommand", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 13,
        "returns_data": False,
        "api_syntax": "LoSetCommand(iCommand, new_value)",
        "parameter_count": 2,
        "parameter_defs": [
            {"id": 0, "name": "iCommand", "type": 0},
            {"id": 1, "name": "new_value", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 14,
        "returns_data": False,
        "api_syntax": "LoGeoCoordinatesToLoCoordinates(longitude_degrees, latitude_degrees)",
        "parameter_count": 2,
        "parameter_defs": [
            {"id": 0, "name": "longitude_degrees", "type": 0},
            {"id": 1, "name": "latitude_degrees", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 15,
        "returns_data": False,
        "api_syntax": "LoCoordinatesToGeoCoordinates(x, z)",
        "parameter_count": 2,
        "parameter_defs": [
            {"id": 0, "name": "x", "type": 0},
            {"id": 1, "name": "z", "type": 0}
        ],
        "result_type": "nil"
    },
    {
        "id": 16,
        "returns_data": True,
        "api_syntax": "list_cockpit_params()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 17,
        "returns_data": True,
        "api_syntax": "LoGetSelfData()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 18,
        "returns_data": True,
        "api_syntax": "LoGetModelTime()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 19,
        "returns_data": True,
        "api_syntax": "LoGetMissionStartTime()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 20,
        "returns_data": True,
        "api_syntax": "LoGetPilotName()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 21,
        "returns_data": True,
        "api_syntax": "LoGetIndicatedAirSpeed()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 22,
        "returns_data": True,
        "api_syntax": "LoGetAccelerationUnits()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 23,
        "returns_data": True,
        "api_syntax": "LoGetADIPitchBankYaw()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 24,
        "returns_data": True,
        "api_syntax": "LoGetSnares()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 25,
        "returns_data": True,
        "api_syntax": "LoGetAltitudeAboveSeaLevel()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 26,
        "returns_data": True,
        "api_syntax": "LoGetAltitudeAboveGroundLevel()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 27,
        "returns_data": True,
        "api_syntax": "LoGetVerticalVelocity()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 28,
        "returns_data": True,
        "api_syntax": "LoGetTrueAirSpeed()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 29,
        "returns_data": True,
        "api_syntax": "LoGetMachNumber()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 30,
        "returns_data": True,
        "api_syntax": "LoGetAngleOfAttack()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 31,
        "returns_data": True,
        "api_syntax": "LoGetGlideDeviation()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 32,
        "returns_data": True,
        "api_syntax": "LoGetSideDeviation()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 33,
        "returns_data": True,
        "api_syntax": "LoGetSlipBallPosition()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 34,
        "returns_data": True,
        "api_syntax": "LoGetEngineInfo()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 35,
        "returns_data": True,
        "api_syntax": "LoGetMechInfo()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 36,
        "returns_data": True,
        "api_syntax": "LoGetControlPanel_HSI()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 37,
        "returns_data": True,
        "api_syntax": "LoGetPayloadInfo()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 38,
        "returns_data": True,
        "api_syntax": "LoGetNavigationInfo()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 39,
        "returns_data": True,
        "api_syntax": "LoGetMagneticYaw()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 40,
        "returns_data": True,
        "api_syntax": "LoGetBasicAtmospherePressure()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 41,
        "returns_data": True,
        "api_syntax": "LoGetMCPState()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 42,
        "returns_data": True,
        "api_syntax": "LoGetTWSInfo()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 43,
        "returns_data": True,
        "api_syntax": "LoGetAngleOfSideSlip()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 44,
        "returns_data": True,
        "api_syntax": "LoGetRadarAltimeter()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 45,
        "returns_data": True,
        "api_syntax": "LoGetRoute()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 46,
        "returns_data": True,
        "api_syntax": "LoGetWingInfo()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 47,
        "returns_data": True,
        "api_syntax": "LoGetRadioBeaconsStatus()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 48,
        "returns_data": True,
        "api_syntax": "LoGetVectorVelocity()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 49,
        "returns_data": True,
        "api_syntax": "LoGetVectorWindVelocity()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 50,
        "returns_data": True,
        "api_syntax": "LoGetAngularVelocity()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 51,
        "returns_data": True,
        "api_syntax": "LoGetFMData()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 52,
        "returns_data": True,
        "api_syntax": "LoGetWorldObjects()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 53,
        "returns_data": True,
        "api_syntax": "LoGetTargetInformation()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 54,
        "returns_data": True,
        "api_syntax": "LoGetLockedTargetInformation()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 55,
        "returns_data": True,
        "api_syntax": "LoGetF15_TWS_Contacts()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 56,
        "returns_data": True,
        "api_syntax": "LoGetSightingSystemInfo()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 57,
        "returns_data": True,
        "api_syntax": "LoGetWingTargets()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 58,
        "returns_data": True,
        "api_syntax": "LoGetAltitude()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 59,
        "returns_data": True,
        "api_syntax": "LoIsOwnshipExportAllowed()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 60,
        "returns_data": True,
        "api_syntax": "LoIsObjectExportAllowed()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    },
    {
        "id": 61,
        "returns_data": True,
        "api_syntax": "LoIsSensorExportAllowed()",
        "parameter_count": 0,
        "parameter_defs": [],
        "result_type": "nil"
    }
]
    