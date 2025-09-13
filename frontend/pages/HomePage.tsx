import React from 'react';
import { Button } from '../components/ui';
import { MOCK_SERVICES, MOCK_CATEGORIES } from '../services/api';
import { BriefcaseIcon, UsersIcon, PlusCircleIcon } from '../components/icons';

// Componente MetricCard del original
const MetricCard: React.FC<{ title: string; value: string; description: string; icon: React.ReactNode }> = ({ title, value, description, icon }) => (
    <div className="text-center p-6 bg-white rounded-xl shadow-md border border-slate-200/80">
        <div className="flex justify-center mb-4 text-primary-600">
            {icon}
        </div>
        <h3 className="text-2xl font-bold text-slate-900 mb-2">{value}</h3>
        <h4 className="text-lg font-semibold text-slate-700 mb-2">{title}</h4>
        <p className="text-slate-600">{description}</p>
    </div>
);

// Componente ServiceCard del original
const ServiceCard: React.FC<{ service: any }> = ({ service }) => (
    <div className="bg-white rounded-xl shadow-md border border-slate-200/80 overflow-hidden hover:shadow-lg transition-shadow duration-200">
        <div className="p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-900">{service.name}</h3>
                <span className="text-sm text-slate-500">{service.category}</span>
            </div>
            <p className="text-slate-600 mb-4">{service.description}</p>
            <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-primary-600">{service.price}</span>
                <div className="flex items-center">
                    <span className="text-yellow-400">★</span>
                    <span className="ml-1 text-sm text-slate-600">{service.rating}</span>
                </div>
            </div>
        </div>
    </div>
);

const HomePage: React.FC = () => {
    return (
        <div className="bg-white">
            {/* Hero Section */}
            <section className="relative">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32 flex flex-col md:flex-row items-center">
                    <div className="md:w-1/2 text-center md:text-left">
                        <h1 className="text-4xl md:text-6xl font-extrabold text-slate-900 leading-tight tracking-tighter">
                            Conectá, colaborá y hacé <span className="text-primary-600">crecer tu negocio.</span>
                        </h1>
                        <p className="mt-6 text-lg text-slate-600 max-w-xl mx-auto md:mx-0">
                            Publicá tus servicios o encontrá proveedores calificados en un solo lugar. La plataforma SEVA Empresas líder en Paraguay.
                        </p>
                        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
                            <Button to="/marketplace" variant="secondary" className="text-lg">Explorar el marketplace</Button>
                        </div>
                    </div>
                    <div className="md:w-1/2 mt-12 md:mt-0 flex justify-center">
                        <img src="https://images.unsplash.com/photo-1556761175-5973dc0f32e7?q=80&w=1932&auto=format&fit=crop" alt="Business collaboration" className="rounded-2xl shadow-2xl w-full max-w-lg object-cover" />
                    </div>
                </div>
            </section>
            
            {/* Metrics Section */}
            <section className="py-20 bg-slate-50">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center">
                        <h2 className="text-3xl font-bold text-slate-900">Construí algo increíble</h2>
                        <p className="mt-4 text-lg text-slate-600 max-w-3xl mx-auto">Accedé a datos clave que muestran cómo esta plataforma puede ayudarte a lanzar y hacer crecer tu negocio más rápido.</p>
                    </div>
                    <div className="mt-12 grid gap-8 md:grid-cols-3">
                       <MetricCard title="Categorías" value="+30" description="Miles de categorías cargadas en la plataforma." icon={<BriefcaseIcon className="w-8 h-8"/>}/>
                       <MetricCard title="Visitas mensuales" value="8K" description="Usuarios y empresas que navegan activamente." icon={<UsersIcon className="w-8 h-8"/>}/>
                       <MetricCard title="Servicios publicados" value="+500" description="Miles de servicios cargados por empresas de distintos rubros." icon={<PlusCircleIcon className="w-8 h-8"/>}/>
                    </div>
                </div>
            </section>

            {/* Latest Services Section */}
            <section className="py-20 bg-white">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center mb-12">
                         <h2 className="text-3xl font-bold text-slate-900">Últimos servicios publicados</h2>
                         <Button to="/marketplace" variant="secondary">Ver todos los servicios</Button>
                    </div>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {MOCK_SERVICES.slice(0, 3).map(service => <ServiceCard key={service.id} service={service} />)}
                    </div>
                </div>
            </section>
            
            {/* Categories Section */}
            <section className="py-20 bg-slate-50">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center">
                        <h2 className="text-3xl font-bold text-slate-900">Explorá por categorías</h2>
                        <p className="mt-4 text-lg text-slate-600 max-w-3xl mx-auto">Encontrá el tipo de servicio que necesitás. Explorá por categoría y descubrí proveedores listos para ayudarte a crecer.</p>
                    </div>
                    <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                        {MOCK_CATEGORIES.map(cat => (
                            <div key={cat.id} className="text-center p-6 bg-white rounded-xl shadow-md border border-slate-200/80 hover:shadow-lg transition-shadow duration-200">
                                <cat.icon className="h-10 w-10 text-primary-600 mx-auto mb-4" />
                                <h3 className="text-lg font-semibold text-slate-900 mb-2">{cat.name}</h3>
                                <p className="text-slate-600">{cat.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>
        </div>
    );
};

export default HomePage;
