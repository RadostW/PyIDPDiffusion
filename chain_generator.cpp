//Copyright 2021 Radost Waszkiewicz
//Permission is hereby granted, free of charge, to any person obtaining a copy 
//of this software and associated documentation files (the "Software"), to deal 
//in the Software without restriction, including without limitation the rights 
//to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
//copies of the Software, and to permit persons to whom the Software is 
//furnished to do so, subject to the following conditions:
//The above copyright notice and this permission notice shall be included in all
//copies or substantial portions of the Software.
//THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
//IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
//FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
//AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
//LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
//SOFTWARE.

#pragma once

#include<random>
#include<cmath>
#include<vector>

std::default_random_engine generator;
std::normal_distribution<double> distribution(0.0,1.0);

double GetNormal()
{
  return distribution(generator);
}

class Point
{
 public:
  double x;
  double y;
  double z;  
  double Norm()
  {
     return sqrt(x*x+y*y+z*z);
  }
  void Normalize()
  {
     double n = Norm();
     x /= n; y /= n; z /= n;
  } 
  Point()
  {
    x=0;y=0;z=0;
  }
  Point add(Point rhs)
  {
    auto ret = Point();
    ret.x = (*this).x + rhs.x;
    ret.y = (*this).y + rhs.y;
    ret.z = (*this).z + rhs.z;
    return ret;    
  }
  Point scale(double rhs)
  {
    auto ret = Point();
    ret.x = (*this).x * rhs;
    ret.y = (*this).y * rhs;
    ret.z = (*this).z * rhs;
    return ret;    
  }

  Point operator+(Point rhs)
  {
    auto ret = Point();
    ret.x = (*this).x + rhs.x;
    ret.y = (*this).y + rhs.y;
    ret.z = (*this).z + rhs.z;
    return ret;
  }
};

Point getSpherical()
{
  auto p = Point();
  while(p.Norm() < 0.0001)
  {
    p.x = GetNormal();
    p.y = GetNormal();
    p.z = GetNormal();
  }
  p.Normalize();
  return p;
}

double squaredDistance(Point a, Point b)
{
  return (a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(a.z-b.z)*(a.z-b.z);
}

double distance(Point a, Point b)
{
  return sqrt(squaredDistance(a,b));
}

typedef std::vector<Point> Chain;
typedef std::vector<double> vdouble;
// Gets a chain of nonoverlapping beads with touching neighbours given specification:
// 'n' -- number of beads
// 'sizes_beg' -- index of first bead size inside 'sizes' vector (very convenient for recursion).
// 'sizes' -- vector of length 'n' with sizes of beads
// Randomizes beads one-by-one with spherically uniform increments. If last bead
// intersects any of the previous ones IT STARTS ALL OVER AGAIN to keep correct 
// distributions of angles.
Chain getChainIterative(int n,int sizes_beg,vdouble sizes)
{
    auto ret = Chain();
    auto end = Point();
    auto candidate = Point();
    // Elongate ret chain until you make it long enough.
    while(ret.size() < n)
    {
        // Try and try again to append points at the end.
        while(true)
        {
            auto step = getSpherical();
            if(ret.size() == 0)
            {
                // Initial point.
                candidate = Point();
            }
            else
            {
                // Noninitial point. Add increment in diretion step at the end of the chain.
                candidate = end.add( step.scale( sizes[ sizes_beg + ret.size() ] + sizes[ sizes_beg + ret.size() - 1]) );
            }
            bool noncrossing = true;
            // For each (but the last) bead in computed chain chech if candidate
            // does not intersect them.
            for(int i = 0; i+1 < ret.size() ; i++)
            {
                if(distance(ret[i],candidate) < sizes[sizes_beg + i]+sizes[sizes_beg + ret.size()])
                {
                    // Failed here no need to check anymore.
                    noncrossing=false;
                    break;
                }
            }
            if(noncrossing)
            {
                // Good candidate. Pop out of the randomizing loop.
                break;
            }
            else // Important! Throw away everything.
            {
                // An intersection found. Damn, start over.
                ret = Chain();
                end = Point();  
            }
        }
        // Add candidate at the end of the chain and update enpoint coordinates.
        ret.push_back(candidate);
        end = candidate;
    }
    return ret;
}


// Gets a chain of nonoverlapping beads with touching neighbours given specification:
// 'n' -- number of beads
// 'sizes_beg' -- index of first bead size inside 'sizes' vector (very convenient for recursion).
// 'sizes' -- vector of length 'n' with sizes of beads
// Randomizes recursively. Randomizes left half and right half separately according
// to the same distribution (note sizes_beg is different in left half and right half)
// and then attempts to put them together. If they intersect it throws both away
// and STARTS FROM SCRATCH to keep distributions of left and right half independent
// (which would not be the case if you re-randomized just some portion of the chain).
Chain getChain(int n,int sizes_beg,vdouble sizes)
{    
    // Chain is very small. Fall back to iterative variant.
    if(n<5)
    {
        return getChainIterative(n,sizes_beg,sizes);
    }
    // Longer chain. Subdivide into two subchains.
    else
    {
        auto ret = Chain();
        while(ret.size() < n)
        {
            auto candidate = Point();
            // Compute lengths of left and right subchains.
            int ml = floor(n/2);
            int mr = n - ml;

            // Get left subchain
            ret = getChain(ml,sizes_beg,sizes);
            auto end_l = ret[ret.size() -1];
            auto step = getSpherical();

            double stepsize = ( sizes[sizes_beg + ml - 1]  + sizes[sizes_beg + ml]);
            // Location of left end of right subchain
            auto beg_r = end_l.add( step.scale( stepsize ) );

            // Get right subchain
            // We'll attempt to add beads from this chain to right chain one-by-one.
            auto app = getChain(mr,ml+sizes_beg,sizes);

            // For each bead in right subchain
            for(int i = 0; i < app.size() ; i++)
            {
                bool noncrossing = true;
                // Possible new bead location: right chain location + end of left chain.
                candidate = app[i].add( beg_r );
                for(int j = 0 ; j + 1 < ret.size() ; j++)
                {
                    auto dist = distance(ret[j],candidate);
                    auto min_dist = (sizes[sizes_beg + j] + sizes[sizes_beg + ml + i]);
                    if(dist < min_dist)
                    {
                        noncrossing=false;
                        break;
                    }
                }
                if(noncrossing)
                {
                    // Good so far. Extend left chain by one bead.
                    ret.push_back(candidate);
                }
                else
                {
                    // Chains intersected. Start over.
                    ret = Chain();
                    beg_r = Point();  
                }
            }
        }
        return ret;    
    }
}
