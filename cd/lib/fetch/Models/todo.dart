// class Todo {
//   int id;
//   String image;
//   DateTime created_at;
//   int originalimage;
//   Todo(
//       {required this.id,
//       required this.image,
//       required this.created_at,
//       required this.originalimage});

//   // Factory method to create a Todo from JSON
//   factory Todo.fromJson(Map<String, dynamic> json) {
//     return Todo(
//         id: json['id'],
//         image: json['processed_image'],
//         created_at: json['created_at'],
//         originalimage: json['original_image']);
//   }
// }

class Todo {
  int id;
  String image; // Full URL for the processed image
  DateTime createdAt; // Parsed DateTime
  int originalImage; // ID of the original image

  Todo({
    required this.id,
    required this.image,
    required this.createdAt,
    required this.originalImage,
  });

  // Factory method to create a Todo from JSON
  factory Todo.fromJson(Map<String, dynamic> json) {
    const String baseUrl =
        "https://your-api-domain.com"; // Replace with your base API URL
    return Todo(
      id: json['id'],
      image: baseUrl +
          json['processed_image'], // Combine base URL with relative path
      createdAt:
          DateTime.parse(json['created_at']), // Parse ISO 8601 date string
      originalImage: json['original_image'], // Map original image ID
    );
  }
}
