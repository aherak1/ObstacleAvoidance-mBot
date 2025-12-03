import 'dart:convert';
import 'package:camera/camera.dart';
import 'package:flutter_blue/flutter_blue.dart';
import 'package:get/get.dart';
import 'package:permission_handler/permission_handler.dart';
import 'mbot.dart';

class BleController extends GetxController {
  FlutterBlue ble = FlutterBlue.instance;
  BluetoothDevice? connectedDevice;
  BluetoothCharacteristic? writeCharacteristic;

  Future scanDevices() async {
    var statusScan = await Permission.bluetoothScan.request();
    var statusConnect = await Permission.bluetoothConnect.request();
    var statusLocation = await Permission.locationWhenInUse.request();

    if (statusScan.isGranted && statusConnect.isGranted && statusLocation.isGranted) {
      print("Sve dozvole su odobrene.");
    } else {
      print("Neke dozvole su odbijene.");
    }
    ble.startScan(timeout: const Duration(seconds: 10));
  }

  Future<void> connectToDevice(BluetoothDevice device) async {
    await device.connect(timeout: const Duration(seconds: 15));

    device.state.listen((BluetoothDeviceState state) async {
      if (state == BluetoothDeviceState.connected) {
        print("Device connected: ${device.name}");
        connectedDevice = device;
        discoverServices();


          Get.to(() => const CommandReceiverScreen());

      } else {
        print("Device Disconnected");
      }
    });
  }


  Future<void> discoverServices() async {
    if (connectedDevice != null) {
      List<BluetoothService> services = await connectedDevice!.discoverServices();
      for (BluetoothService service in services) {
        for (BluetoothCharacteristic characteristic in service.characteristics) {
          if (characteristic.properties.write) {
            writeCharacteristic = characteristic;
            return;
          }
        }
      }
    }
  }

  void sendMovementCommand(String command) async {
    if (writeCharacteristic != null) {
      List<int> commandBytes = _convertCommandToBytes(command);
      await writeCharacteristic!.write(commandBytes);
    } else {
      print('Bluetooth karakteristika nije dostupna');
    }
  }

  List<int> _convertCommandToBytes(String command) {
    print(command);
    switch (command) {
      case 'left':
        return _createDriveCommand(100, 100);
      case 'right':
        return _createDriveCommand(-100, -100);
      case 'forward':
        return _createDriveCommand(-75, 75);
      case 'backward':
        return _createDriveCommand(100, -100);
      default:
        return _createDriveCommand(0, 0);
    }
  }

  List<int> _createDriveCommand(int powerLeft, int powerRight) {
    if(powerLeft-90>0 && powerRight-90>0) {
      return [
      0xff, 0x55, 0x07, 0x00, 0x02, 0x05,
      powerLeft & 0xff,
      (
      (powerLeft-74) >> 2048) & 0xff,
      powerRight & 0xff,
      ((powerRight-74) >> 2048) & 0xff,
    ];
    }
    return [
      0xff, 0x55, 0x07, 0x00, 0x02, 0x05,
      powerLeft & 0xff,
      (
          (powerLeft) >> 2048) & 0xff,
      powerRight & 0xff,
      ((powerRight) >> 2048) & 0xff,
    ];
  }

  Stream<List<ScanResult>> get scanResults => ble.scanResults;

  void stopScan() {
    ble.stopScan();
  }
}
