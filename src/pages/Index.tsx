import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

const Index = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 800 * 400) {
        toast({
          title: 'Файл слишком большой',
          description: 'Максимальный размер 800x400px',
          variant: 'destructive',
        });
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string);
        setGeneratedImage(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string);
        setGeneratedImage(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleGenerate = async () => {
    if (!selectedImage) {
      toast({
        title: 'Загрузите фото',
        description: 'Сначала выберите изображение',
        variant: 'destructive',
      });
      return;
    }

    setIsGenerating(true);
    
    setTimeout(() => {
      setGeneratedImage(selectedImage);
      setIsGenerating(false);
      toast({
        title: 'Готово!',
        description: 'Открытка сгенерирована',
      });
    }, 2000);
  };

  const handleDownload = () => {
    if (generatedImage) {
      const link = document.createElement('a');
      link.href = generatedImage;
      link.download = 'babushkin-generator.png';
      link.click();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FF69B4] via-[#FFB6D9] to-[#FFFSFF] py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-5xl md:text-6xl font-bubblegum text-center mb-8 text-[#FF1493] drop-shadow-lg animate-fade-in">
          Бабушкин Генератор Открыток
        </h1>

        <div className="bg-white/90 backdrop-blur-sm rounded-3xl p-8 shadow-2xl animate-scale-in">
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            className="border-4 border-dashed border-[#FFB6D9] rounded-2xl p-12 mb-6 cursor-pointer hover:border-[#FF69B4] hover:bg-[#FFFSFF]/50 transition-all duration-300 min-h-[300px] flex flex-col items-center justify-center"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/gif"
              onChange={handleFileChange}
              className="hidden"
            />
            
            {selectedImage ? (
              <div className="w-full animate-fade-in">
                <img
                  src={selectedImage}
                  alt="Загруженное фото"
                  className="max-w-full max-h-[400px] mx-auto rounded-xl shadow-lg"
                />
                <p className="text-center mt-4 text-[#FF1493] font-medium">
                  Нажмите для смены фото
                </p>
              </div>
            ) : (
              <div className="text-center">
                <Icon name="CloudUpload" size={64} className="mx-auto mb-4 text-[#FFB6D9]" />
                <p className="text-xl text-gray-600 font-medium mb-2">
                  Нажмите для загрузки или перетащите фото
                </p>
                <p className="text-sm text-gray-500">
                  PNG, JPG, GIF (MAX. 800x400px)
                </p>
              </div>
            )}
          </div>

          <div className="mb-6">
            <label className="block text-lg font-medium text-[#FF1493] mb-2">
              Промпт для генерации (настраивается)
            </label>
            <Textarea
              placeholder="Здесь будет промпт для стилизации изображения через Gemini API..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="min-h-[100px] text-base border-[#FFB6D9] focus:border-[#FF69B4] rounded-xl"
            />
            <p className="text-sm text-gray-500 mt-2">
              💡 Промпт будет автоматически применяться к загруженному фото
            </p>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={!selectedImage || isGenerating}
            className="w-full bg-gradient-to-r from-[#FF69B4] to-[#FF1493] hover:from-[#FF1493] hover:to-[#FF69B4] text-white font-bold text-lg py-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <Icon name="Loader2" className="mr-2 h-5 w-5 animate-spin" />
                Генерируем открытку...
              </>
            ) : (
              <>
                <Icon name="Sparkles" className="mr-2 h-5 w-5" />
                Создать открытку
              </>
            )}
          </Button>

          {generatedImage && (
            <div className="mt-8 animate-fade-in">
              <h2 className="text-2xl font-bubblegum text-[#FF1493] mb-4 text-center">
                Ваша открытка готова! 🎉
              </h2>
              <div className="relative">
                <img
                  src={generatedImage}
                  alt="Сгенерированная открытка"
                  className="w-full rounded-xl shadow-2xl"
                />
              </div>
              <Button
                onClick={handleDownload}
                className="w-full mt-4 bg-[#FFB6D9] hover:bg-[#FF69B4] text-[#FF1493] font-bold text-lg py-4 rounded-xl"
              >
                <Icon name="Download" className="mr-2 h-5 w-5" />
                Скачать открытку
              </Button>
            </div>
          )}
        </div>

        <div className="mt-8 text-center text-white/80">
          <p className="text-sm">
            Создавайте уникальные открытки с помощью искусственного интеллекта ✨
          </p>
        </div>
      </div>
    </div>
  );
};

export default Index;
