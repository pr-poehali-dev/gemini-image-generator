import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

interface GenerationData {
  count: number;
  date: string;
}

const BACKEND_URL = 'https://functions.poehali.dev/937cd074-b42c-4c14-86bc-4a8b85463284';

const Index = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationsLeft, setGenerationsLeft] = useState(3);
  const [customText, setCustomText] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    const data = localStorage.getItem('generationData');
    if (data) {
      const parsed: GenerationData = JSON.parse(data);
      const today = new Date().toDateString();
      
      if (parsed.date === today) {
        setGenerationsLeft(Math.max(0, 3 - parsed.count));
      } else {
        localStorage.setItem('generationData', JSON.stringify({ count: 0, date: today }));
        setGenerationsLeft(3);
      }
    } else {
      const today = new Date().toDateString();
      localStorage.setItem('generationData', JSON.stringify({ count: 0, date: today }));
    }
  }, []);

  const updateGenerationCount = () => {
    const data = localStorage.getItem('generationData');
    const today = new Date().toDateString();
    
    if (data) {
      const parsed: GenerationData = JSON.parse(data);
      if (parsed.date === today) {
        const newCount = parsed.count + 1;
        localStorage.setItem('generationData', JSON.stringify({ count: newCount, date: today }));
        setGenerationsLeft(Math.max(0, 3 - newCount));
      } else {
        localStorage.setItem('generationData', JSON.stringify({ count: 1, date: today }));
        setGenerationsLeft(2);
      }
    } else {
      localStorage.setItem('generationData', JSON.stringify({ count: 1, date: today }));
      setGenerationsLeft(2);
    }
  };

  const resizeImage = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');
          
          const maxWidth = 800;
          const maxHeight = 800;
          let width = img.width;
          let height = img.height;
          
          if (width > maxWidth || height > maxHeight) {
            const ratio = Math.min(maxWidth / width, maxHeight / height);
            width = width * ratio;
            height = height * ratio;
          }
          
          canvas.width = width;
          canvas.height = height;
          ctx?.drawImage(img, 0, 0, width, height);
          resolve(canvas.toDataURL('image/jpeg', 0.9));
        };
        img.src = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    });
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const resized = await resizeImage(file);
      setSelectedImage(resized);
      setGeneratedImage(null);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      const resized = await resizeImage(file);
      setSelectedImage(resized);
      setGeneratedImage(null);
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

    if (generationsLeft <= 0) {
      toast({
        title: 'Лимит исчерпан',
        description: 'Вы использовали все 3 генерации на сегодня',
        variant: 'destructive',
      });
      return;
    }

    setIsGenerating(true);
    
    try {
      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          imageBase64: selectedImage,
          customText: customText.trim() || undefined,
        }),
      });

      const data = await response.json();
      
      if (data.success && data.imageUrl) {
        setGeneratedImage(data.imageUrl);
        updateGenerationCount();
        toast({
          title: 'Готово!',
          description: 'Открытка сгенерирована через NanoBanana AI',
        });
      } else {
        throw new Error(data.error || 'Generation failed');
      }
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось сгенерировать открытку. Проверьте API ключ.',
        variant: 'destructive',
      });
    } finally {
      setIsGenerating(false);
    }
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
    <>
      <div className="bg-gradient-to-r from-[#FF8C42] to-[#FFA500] py-2 px-4 text-center">
        <p className="text-sm font-medium text-white">
          🚀 Создано за 2 часа на{' '}
          <a 
            href="https://poehali.dev" 
            target="_blank" 
            rel="noopener noreferrer"
            className="underline hover:text-gray-100 transition-colors"
          >
            poehali.dev
          </a>
        </p>
      </div>
      <div className="min-h-[calc(100vh-36px)] bg-gradient-to-br from-[#FF69B4] via-[#FFB6D9] to-[#FFFSFF] flex items-center justify-center py-8 px-4">
        <div className="max-w-3xl w-full">
        <h1 className="text-5xl md:text-6xl font-handwritten font-bold text-center mb-6 text-[#FF1493] drop-shadow-lg animate-fade-in">
          Бабушкин Генератор Открыток
        </h1>

        <div className="bg-white/90 backdrop-blur-sm rounded-3xl p-6 shadow-2xl animate-scale-in">
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            className="border-4 border-dashed border-[#FFB6D9] rounded-2xl mb-6 cursor-pointer hover:border-[#FF69B4] hover:bg-[#FFFSFF]/50 transition-all duration-300 h-[400px] flex flex-col items-center justify-center p-6"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/gif"
              onChange={handleFileChange}
              className="hidden"
            />
            
            {generatedImage ? (
              <div className="w-full h-full flex flex-col items-center justify-center animate-fade-in">
                <img
                  src={generatedImage}
                  alt="Сгенерированная открытка"
                  className="max-w-full max-h-[90%] object-contain rounded-xl shadow-lg"
                />
                <p className="text-center mt-4 text-[#FF1493] font-medium">
                  Нажмите для загрузки нового фото
                </p>
              </div>
            ) : selectedImage ? (
              <div className="w-full h-full flex flex-col items-center justify-center animate-fade-in">
                <img
                  src={selectedImage}
                  alt="Загруженное фото"
                  className="max-w-full max-h-[90%] object-contain rounded-xl shadow-lg"
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
                  PNG, JPG, GIF (любого размера)
                </p>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#FF1493] mb-2">
                Пожелание (необязательно)
              </label>
              <Textarea
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                placeholder="Например: С Днём Рождения! Счастья, здоровья, всех благ!"
                className="resize-none border-[#FFB6D9] focus:border-[#FF69B4] min-h-[80px]"
                maxLength={200}
              />
              <p className="text-xs text-gray-500 mt-1">
                {customText.length} / 200 символов
              </p>
            </div>

            <div className="text-center">
              <p className="text-lg font-bold text-[#FF1493]">
                Осталось генераций сегодня: {generationsLeft} / 3
              </p>
            </div>
            
            <Button
              onClick={handleGenerate}
              disabled={!selectedImage || isGenerating || generationsLeft <= 0}
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
          </div>

          {generatedImage && (
            <div className="mt-8 animate-fade-in">
              <Button
                onClick={handleDownload}
                className="w-full bg-[#FFB6D9] hover:bg-[#FF69B4] text-[#FF1493] font-bold text-lg py-4 rounded-xl"
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
    </>
  );
};

export default Index;