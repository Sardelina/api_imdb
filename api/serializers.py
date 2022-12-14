from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .custom_authentication import AuthenticationWithoutPassword
from .models import User, Review, Comment, Category, Genre, Title


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('first_name', 'last_name', 'username', 'bio', 'email', 'role')
        model = User


class UserLoginSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('email',)
        model = User


class TokenWithoutPasswordSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_code = kwargs['data']['confirmation_key']
        self.fields['password'].required = False

    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
        }
        try:
            authenticate_kwargs['request'] = self.context['request']
        except KeyError:
            pass
        self.user = AuthenticationWithoutPassword().authenticate(
            **authenticate_kwargs
        )
        if self.user.confirmation_key != self.request_code:
            data = {'error': 'confirmation_code is not valid'}
        else:
            refresh = self.get_token(self.user)
            data = {'token': str(refresh.access_token)}
        return data


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.CharField(
        allow_blank=False,
        validators=[UniqueValidator(queryset=Category.objects.all())]
    )

    class Meta:
        fields = ('name', 'slug')
        model = Category


class GenreSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(
        allow_blank=False,
        validators=[UniqueValidator(queryset=Genre.objects.all())]
    )

    class Meta:
        fields = ('name', 'slug')
        model = Genre


class TitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.ReadOnlyField()

    class Meta:
        fields = ('id', 'name', 'year', 'rating', 'description', 'category', 'genre')
        model = Title

    def check_category_genre(self, category, genre):
        if category:
            real_category = Category.objects.filter(slug=category)
            if not real_category:
                raise serializers.ValidationError(
                    f'{category} category does not exist'
                )
        else:
            real_category = None
        genres = []
        genre_list = genre
        for genre_slug in genre_list:
            real_genre = Genre.objects.filter(slug=genre_slug)
            if real_genre:
                genres.append(get_object_or_404(Genre, slug=genre_slug))
            else:
                raise serializers.ValidationError(
                    f'{genre_slug} genre does not exist')
        return real_category, genres


class ReviewsSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        many=False,
        slug_field='pk',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        many=False,
        slug_field='username',
        read_only=True,
    )

    class Meta:
        fields = ('id','title', 'text', 'author', 'score', 'pub_date')
        model = Review


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date')
        model = Comment
