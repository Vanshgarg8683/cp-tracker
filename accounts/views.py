from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # allows public access
from .serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]  # no login required
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)  # take input
    
    
        if serializer.is_valid():
            serializer.save()  # save user
            return Response({"msg": "User created"}, status=201)
        
        return Response(serializer.errors, status=400)  # return errors

