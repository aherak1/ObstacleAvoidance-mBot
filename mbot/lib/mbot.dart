import 'dart:convert';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:get/get.dart';
import 'ble_controller.dart';

class CommandReceiverScreen extends StatefulWidget {
  const CommandReceiverScreen({super.key});

  @override
  _CommandReceiverScreenState createState() => _CommandReceiverScreenState();
}

class _CommandReceiverScreenState extends State<CommandReceiverScreen> {
  final BleController _bleController = Get.find();
  Timer? _timer;
  bool _isProcessingCommand = false;
  @override
  void initState() {
    super.initState();
    _startListeningForCommands();
  }

  void _startListeningForCommands() {
    _timer = Timer.periodic(Duration(milliseconds: 100), (Timer t) async {
      if (_isProcessingCommand) {
        return;
      }

      try {
        final response = await http.post(Uri.parse('http://192.168.0.12:6000/get_command'));

        if (response.statusCode == 200) {
          final Map<String, dynamic> jsonResponse = json.decode(response.body);
          String moveCommand = _determineMovementCommand(jsonResponse);
          _isProcessingCommand = true;
          await _sendMovementCommand(moveCommand);

        } else {
          print("Failed to receive command: ${response.statusCode}");
        }
      } catch (e) {
        _bleController.sendMovementCommand(("stop"));
        print("Error receiving command: $e");
      }
    });
  }

  String _determineMovementCommand(Map<String, dynamic> jsonResponse) {
    if (jsonResponse.containsKey('command')) {
      return jsonResponse['command'];
    }
    return 'forward';
  }

  Future<void> _sendMovementCommand(String command) async {
    _isProcessingCommand=true;
    if (command == 'move_forward') {
       _bleController.sendMovementCommand('forward');
       _isProcessingCommand=false;
    } else if (command == 'move_right') {
      _isProcessingCommand=true;
      await _executeMoveRightSequence();
    } else if (command == 'move_left') {
      _isProcessingCommand=true;
      await _executeMoveLeftSequence();
    } else {

      print("Unknown command: $command");
      _bleController.sendMovementCommand("stop");
      _isProcessingCommand=false;

    }
  }


  Future<void> _executeMoveRightSequence() async {
    await Future.delayed(Duration(milliseconds: 500));
    _bleController.sendMovementCommand('right');
    await Future.delayed(Duration(milliseconds: 1000));
    _bleController.sendMovementCommand('forward');
    await Future.delayed(Duration(seconds: 2));
    _bleController.sendMovementCommand('left');
    await Future.delayed(Duration(milliseconds: 1200));
    _bleController.sendMovementCommand('forward');
    await Future.delayed(Duration(seconds: 5));
    _bleController.sendMovementCommand('left');
    await Future.delayed(Duration(milliseconds: 1000));
    _bleController.sendMovementCommand('forward');
    await Future.delayed(Duration(seconds: 2));
    _bleController.sendMovementCommand('right');
    await Future.delayed(Duration(milliseconds: 1000));
    _bleController.sendMovementCommand('forward');
    _isProcessingCommand=false;
  }

  Future<void> _executeMoveLeftSequence() async {
    await Future.delayed(Duration(milliseconds: 500));
    _bleController.sendMovementCommand('left');
    await Future.delayed(Duration(milliseconds: 1000));
    _bleController.sendMovementCommand('forward');
    await Future.delayed(Duration(seconds: 2));
    _bleController.sendMovementCommand('right');
    await Future.delayed(Duration(milliseconds: 1000));
    _bleController.sendMovementCommand('forward');
    await Future.delayed(Duration(seconds: 5));
    _bleController.sendMovementCommand('right');
    await Future.delayed(Duration(milliseconds: 1000));
    _bleController.sendMovementCommand('forward');
    await Future.delayed(Duration(seconds: 2));
    _bleController.sendMovementCommand('left');
    await Future.delayed(Duration(milliseconds: 1000));
    _bleController.sendMovementCommand('forward');
    _isProcessingCommand=false;
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Command Receiver'),
      ),
      body: Center(
        child: Text('Listening for commands...'),
      ),
    );
  }
}
