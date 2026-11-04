class AppUser {
  const AppUser({
    required this.id,
    required this.username,
    required this.email,
    required this.phoneVerified,
  });
  final String id;
  final String? username;
  final String? email;
  final bool phoneVerified;
  factory AppUser.fromJson(Map<String, dynamic> json) => AppUser(
        id: json['id'] as String,
        username: json['username'] as String?,
        email: json['email'] as String?,
        phoneVerified: json['phone_verified'] as bool? ?? false,
      );
}
