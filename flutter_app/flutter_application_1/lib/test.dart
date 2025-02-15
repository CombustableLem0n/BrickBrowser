import 'package:flutter/material.dart';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart';
import 'package:mime/mime.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const MyHomePage(title: 'Flask/Flutter Hello World'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  String _uploadStatus = 'No image uploaded';

  Future<String> pickAndUploadImage() async {
    final picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);

    if (image == null) {
      return 'No image selected';
    }

    File imageFile = File(image.path);
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('http://127.0.0.1:5000/image'),
    );

    var mimeType = lookupMimeType(imageFile.path) ?? 'image/jpeg';
    request.files.add(
      await http.MultipartFile.fromPath(
        'image',
        imageFile.path,
        contentType: MediaType.parse(mimeType),
      ),
    );

    var response = await request.send();

    if (response.statusCode == 200) {
      return 'Image uploaded successfully';
    } else {
      return 'Failed to upload image';
    }
  }

  void _handleUpload() async {
    String result = await pickAndUploadImage();
    setState(() {
      _uploadStatus = result;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(_uploadStatus),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _handleUpload,
              child: const Text("Select & Upload Image"),
            ),
          ],
        ),
      ),
    );
  }
}
