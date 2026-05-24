from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # allows public access
from .serializers import RegisterSerializer



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        print(request.data)

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "User created"}, status=201)

        return Response(serializer.errors, status=400)

